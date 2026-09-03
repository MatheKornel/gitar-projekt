#include "optimization.h"
#include "fretboard.h"
#include <iostream>
#include <algorithm>

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

double Optimization::ExtraCost(const double currentCenter, const NotePosition &nextPos, const NotePosition &prevPos, const NotePosition &prevPrevPos) const
{
    double extraCost = 0.0;
    std::vector<int> tuning = FretBoard::GetTuning();
    double centerThreshold = tuning.empty() ? 64.0 : (tuning[0] + 24.0);
    if (currentCenter > centerThreshold && nextPos.GetFretIdx() < 5)
    {
        extraCost += 10.0; // ha általában magas hangokat játszünk, akkor feljebb legyen lefogás, a lejjebb lefogásokat büntetjük
    }

    if (prevPos.GetFretIdx() >= 5 && nextPos.GetFretIdx() == 0)
    {
        extraCost += 30.0; // ha az 5. bund felett volt az előző hang, akkor ne váltsunk üres húrra
    }

    const int fretDiff = abs(nextPos.GetFretIdx() - prevPos.GetFretIdx());
    if (prevPos.GetFretIdx() != 0 && nextPos.GetFretIdx() != 0 && fretDiff <= 3)
    {
        extraCost -= 5.0; // ha a kéz egy helyben marad, azt jutalmazzuk
    }

    if ((nextPos.GetStringIdx() == 0 || nextPos.GetStringIdx() == 1) && nextPos.GetFretIdx() > 12)
    {
        extraCost += 500.0; // az E és A húron ne játszunk riffeket a 12. bund felett
    }

    const int stringDiff = abs(prevPos.GetStringIdx() - nextPos.GetStringIdx());
    if (stringDiff > 1)
    {
        extraCost += 500.0 * stringDiff; // húrváltást büntetjük, mert riffeknél nehezebb váltani
    }

    if ((prevPos.GetStringIdx() == 0 && prevPos.GetFretIdx() == 0) || (nextPos.GetStringIdx() == 0 && nextPos.GetFretIdx() == 0))
    {
        extraCost -= 5.0; // ha üres E húr és bármi között van váltás, azt jutalmazzuk, az nem baj
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
    const size_t maxPaths = 25;

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
            double initialCost = 0.0;
            if (!finalPositions.empty())
            {
                NotePosition prevPos = finalPositions.back();
                NotePosition prevPrevPos(-1, -1);
                
                if (finalPositions.size() >= 2)
                {
                    prevPrevPos = finalPositions[finalPositions.size() - 2];
                }
                
                double stepCost = prevPos.Distance(pos);
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
                    const double stepCost = prevPos.Distance(nextPos);
                    const double extraCost = ExtraCost(currentCenter, nextPos, prevPos, prevPrevPos);
                    
                    Path expandedPath = path;
                    expandedPath.positions.push_back(nextPos);
                    expandedPath.totalCost += (stepCost + extraCost);
                    nextPaths.push_back(expandedPath);
                }
            }

            std::sort(nextPaths.begin(), nextPaths.end(), [](const Path &a, const Path &b)
                      { return a.totalCost < b.totalCost; });
            if (nextPaths.size() > maxPaths)
            {
                nextPaths.resize(maxPaths);
            }

            currentPaths = nextPaths;
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