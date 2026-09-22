#include "optimization.h"
#include "fretboard.h"
#include <iostream>
#include <algorithm>
#include <cmath>
#include <map>
struct Path
{
    std::vector<NotePosition> positions;
    double totalCost = 0.0;
};

Optimization::Optimization(const std::vector<InputNotes> &newNotes) : notes(std::move(newNotes)) {}

double Optimization::CalculateCenter(const size_t currentIdx)
{
    const double timeWindow = 2.0; // 2 másodperc előre
    const double currentOnset = notes[currentIdx].GetOnset();
    std::vector<int> windowMidis;

    for (size_t i = currentIdx; i < notes.size(); i++)
    {
        if (notes[i].GetOnset() - currentOnset > timeWindow)
        {
            break;
        }

        if (i > currentIdx)
        {
            double prevOffset = notes[i - 1].GetOnset() + notes[i - 1].GetDuration();
            if (notes[i].GetOnset() - prevOffset > 0.4)
            {
                break;
            }
        }

        windowMidis.push_back(notes[i].GetMidiNote());
    }

    if (windowMidis.empty())
        return 0.0;

    std::sort(windowMidis.begin(), windowMidis.end());
    size_t mid = windowMidis.size() / 2;

    if (windowMidis.size() % 2 == 0)
    {
        return (windowMidis[mid - 1] + windowMidis[mid]) / 2.0;
    }
    else
    {
        return windowMidis[mid];
    }
}

double Optimization::InitialFretPenalty(const NotePosition& pos) const
{
    return pos.GetFretIdx() * 0.01;
}

double Optimization::ExtraCost(const double currentCenter, const NotePosition &nextPos, const NotePosition &prevPos, const NotePosition &prevPrevPos) const
{
    double extraCost = 0.0;
    std::vector<int> tuning = FretBoard::GetTuning();
    double centerThreshold = tuning.empty() ? 64.0 : (tuning[0] + 24.0);
    if (currentCenter > centerThreshold && nextPos.GetFretIdx() < 3)
    {
        extraCost += 5.0; // ha általában magas hangokat játszünk, akkor feljebb legyen lefogás, a lejjebb lefogásokat büntetjük
    }

    if (prevPos.GetFretIdx() >= 5 && nextPos.GetFretIdx() == 0 && nextPos.GetStringIdx() > 1)
    {
        extraCost += prevPos.GetFretIdx() * 2.0; // az E és A húrra nem érvényes a büntetés, de a többi húrra igen, ha az előző hang 5. bund felett volt, akkor ne váltsunk üres húrra
    }

    const int fretDiff = abs(nextPos.GetFretIdx() - prevPos.GetFretIdx());
    if (fretDiff <= 3 && !(prevPos.GetFretIdx() == 0 && nextPos.GetFretIdx() != 0 && abs(nextPos.GetFretIdx() - prevPrevPos.GetFretIdx()) > 4)) 
    {
         extraCost -= 5.0; // ha ugyanazon a húron vagyunk, vagy a bundtávolság kicsi (kéz egy helyben marad jutalom)
    }

    if ((nextPos.GetStringIdx() == 0 || nextPos.GetStringIdx() == 1) && nextPos.GetFretIdx() > 12)
    {
        extraCost += 25.0; // az E és A húron ne játszunk riffeket a 12. bund felett
    }

    if (nextPos.GetFretIdx() == 0 && nextPos.GetStringIdx() >= 2)
    {
        extraCost += 15.0; // vékony húrokat ne játsza üresen riffek közben
    }

    const int stringDiff = abs(prevPos.GetStringIdx() - nextPos.GetStringIdx());
    // húrváltás büntetés
    if (stringDiff == 1)
    {
        extraCost += 8.0;
    }
    else if (stringDiff > 1)
    {
        extraCost += 25.0 * (stringDiff - 1);
    }

    bool isPrevPedal = (prevPos.GetFretIdx() == 0 && prevPos.GetStringIdx() <= 1);
    bool isNextPedal = (nextPos.GetFretIdx() == 0 && nextPos.GetStringIdx() <= 1);
    if (isPrevPedal || isNextPedal)
    {
        extraCost -= 5.0; // csak a vastag pedálhúrokat (E és A) jutalmazzuk, ha onnan jövünk vagy oda megyünk
    }

    if (prevPrevPos.GetFretIdx() != -1) // ha V alakú, oda vissza ugrálások vannak, büntetjük
    {
        int fret1 = prevPrevPos.GetFretIdx();
        int fret2 = prevPos.GetFretIdx();
        int fret3 = nextPos.GetFretIdx();

        if (fret1 != 0 && fret2 != 0 && fret3 != 0)
        {
            bool upThenDown = (fret2 > fret1) && (fret3 < fret2);
            bool downThenUp = (fret2 < fret1) && (fret3 > fret2);

            if (upThenDown || downThenUp)
            {
                int jump1 = abs(fret2 - fret1);
                int jump2 = abs(fret3 - fret2);
                int lowestFret = std::min(fret1, std::min(fret2, fret3));

                int jumpTolerance = 3;

                if (lowestFret >= 12)
                    jumpTolerance = 4;
                if (lowestFret >= 17)
                    jumpTolerance = 5;

                if (jump1 >= jumpTolerance && jump2 >= jumpTolerance)
                {
                    extraCost += 15.0;
                }
            }
        }
    }

    return extraCost;
}

std::vector<NotePosition> Optimization::RunOptimization()
{
    std::vector<NotePosition> finalPositions;
    finalPositions.reserve(notes.size());

    const int windowSize = 10;

    for (size_t i = 0; i < notes.size(); i++)
    {
        std::vector<InputNotes> window;
        for (size_t j = i; j < i + windowSize && j < notes.size(); j++)
        {
            window.push_back(notes[j]);
        }

        std::vector<Path> currentPaths;
        auto firstNotePositions = FretBoard::GetPositions(window[0].GetMidiNote());

        if (firstNotePositions.empty())
        {
            std::cerr << "Nem talalhato lefogas a " << window[0].GetMidiNote() << " hanghoz!" << std::endl;
            finalPositions.push_back(NotePosition(0, 0));
            continue;
        }

        double currentCenter = CalculateCenter(i);

        for (const auto &pos : firstNotePositions)
        {
            double initialCost = InitialFretPenalty(pos);
            if (!finalPositions.empty())
            {
                NotePosition prevPos = finalPositions.back();
                NotePosition prevPrevPos(-1, -1);
                
                if (finalPositions.size() >= 2)
                {
                    prevPrevPos = finalPositions[finalPositions.size() - 2];
                }
                
                double ioi = notes[i].GetOnset() - notes[i - 1].GetOnset();
                double urgency = std::clamp(std::sqrt(0.25 / std::max(ioi, 0.03)), 0.6, 4.0);

                double stepCost = prevPos.Distance(pos) * urgency;
                double extraCost = ExtraCost(currentCenter, pos, prevPos, prevPrevPos);
                
                initialCost = stepCost + extraCost;
            }
            Path newPath;
            newPath.positions.push_back(pos);
            newPath.totalCost = initialCost;
            currentPaths.push_back(newPath);
        }

        for (size_t j = 1; j < window.size(); j++)
        {
            auto nextPositions = FretBoard::GetPositions(window[j].GetMidiNote());
            std::vector<Path> nextPaths;

            double ioi = window[j].GetOnset() - window[j - 1].GetOnset();
            double urgency = std::clamp(std::sqrt(0.25 / std::max(ioi, 0.03)), 0.6, 4.0);

            double dynamicCenter = CalculateCenter(i + j);

            for (const auto &path : currentPaths)
            {
                const auto &prevPos = path.positions.back();

                NotePosition prevPrevPos(-1, -1);
                if (path.positions.size() >= 2)
                {
                    prevPrevPos = path.positions[path.positions.size() - 2];
                }
                else if (!finalPositions.empty())
                {
                    prevPrevPos = finalPositions.back();
                }

                for (const auto &nextPos : nextPositions)
                {
                    const double stepCost = prevPos.Distance(nextPos) * urgency;
                    const double extraCost = ExtraCost(dynamicCenter, nextPos, prevPos, prevPrevPos);
                    
                    Path expandedPath = path;
                    expandedPath.positions.push_back(nextPos);
                    expandedPath.totalCost += (stepCost + extraCost);
                    nextPaths.push_back(expandedPath);
                }
            }

            std::map<std::pair<int, int>, Path> bestStatePaths;

            for (const auto &p : nextPaths)
            {
                // vesszük az útvonal utolsó két lefogását, hogy meghatározzuk a kéz fizikai állapotát
                NotePosition currPos = p.positions.back();
                NotePosition prevPos(-1, -1);
                
                if (p.positions.size() >= 2) 
                {
                    prevPos = p.positions[p.positions.size() - 2]; // ha ablakon belül vagyunk
                } 
                else if (!finalPositions.empty()) 
                {
                    prevPos = finalPositions.back(); // ha az ablak legelső lépése
                }

                // egyedi azonosítót generálunk a lefogásokból (pl A húr 7. bund -> 107)
                int prevId = (prevPos.GetFretIdx() != -1) ? (prevPos.GetStringIdx() * 100 + prevPos.GetFretIdx()) : -1;
                int currId = currPos.GetStringIdx() * 100 + currPos.GetFretIdx();
                std::pair<int, int> stateKey = {prevId, currId};

                // ha nincs ilyen állapot, elmenti, ha pedig van, akkor csak akkor frissíti, ha az új útvonal költsége kisebb, mint a korábbi
                if (bestStatePaths.find(stateKey) == bestStatePaths.end() || p.totalCost < bestStatePaths[stateKey].totalCost)
                {
                    bestStatePaths[stateKey] = p;
                }
            }

            // visszatöltjük a legjobb útvonalakat, így a következő iterációban már csak a legjobbakat vizsgáljuk
            currentPaths.clear();
            for (const auto &pair : bestStatePaths)
            {
                currentPaths.push_back(pair.second);
            }
        }

        double bestCost = std::numeric_limits<double>::max();
        std::vector<NotePosition> bestWindowPath;

        for (const auto &path : currentPaths)
        {
            if (path.totalCost < bestCost)
            {
                bestCost = path.totalCost;
                bestWindowPath = path.positions;
            }
        }

        if (!bestWindowPath.empty())
        {
            finalPositions.push_back(bestWindowPath[0]);
        }
        else
        {
            std::cerr << "Nem talalhato ervenyes utvonal a(z) " << i
                      << ". hangtol (MIDI " << notes[i].GetMidiNote()
                      << ") kezdodo ablakhoz - kimaradt az eredmenybol!" << std::endl;
        }
    }

    return finalPositions;
}