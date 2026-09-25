#include "optimization.h"
#include "fretboard.h"
#include <iostream>
#include <algorithm>
#include <cmath>
#include <map>
#include <tuple>
struct Path
{
    std::vector<NotePosition> positions;
    std::vector<int> handFrets; // a kéz pozíciója (mutatóujj bundja) minden hangnál, -1 ha még nem ismert
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

std::vector<int> Optimization::PossibleHandFrets(const NotePosition &pos, const int prevHandFret) const
{
    std::vector<int> handFrets;

    // üres húrnál nem kell lefogni semmit, a kéz ott marad, ahol volt
    if (pos.GetFretIdx() == 0)
    {
        handFrets.push_back(prevHandFret);
        return handFrets;
    }

    // a kéz 4 bundot fog át (1 ujj / bund), így a hangot a mutató-, közép-, gyűrűs- vagy kisujj is lefoghatja
    const int handSpan = 3;
    for (int handFret = std::max(1, pos.GetFretIdx() - handSpan); handFret <= pos.GetFretIdx(); handFret++)
    {
        handFrets.push_back(handFret);
    }
    return handFrets;
}

double Optimization::HandCost(const int prevHandFret, const NotePosition &nextPos, const int nextHandFret) const
{
    const double handWeight = 5.0;   // kézmozgás büntetés bundonként
    const double pinkyPenalty = 1.0; // a kisujj gyengébb, enyhén büntetjük

    double cost = 0.0;

    // csak akkor van kézmozgás, ha mindkét kézpozíció ismert (üres húroknál a kéz nem mozdul)
    if (prevHandFret != -1 && nextHandFret != -1 && prevHandFret != nextHandFret)
    {
        const int handDiff = abs(nextHandFret - prevHandFret);
        cost += handWeight * handDiff;

        // menzúra mm-ben (a 648 mm a tipikus gitár menzúra)
        const double L = 648.0;

        // a kéz két pozíciójának fizikai távolsága a nyeregtől (mm)
        double prevHandMm = L * (1.0 - std::pow(2.0, -prevHandFret / 12.0));
        double nextHandMm = L * (1.0 - std::pow(2.0, -nextHandFret / 12.0));

        // a kéz elmozdulása mm-ben
        double shiftMm = std::abs(prevHandMm - nextHandMm);

        // kb 100 mm felett már nagy ugrásnak számít, mm-ként büntetjük
        const double maxShiftMm = 100.0;
        if (shiftMm > maxShiftMm)
        {
            cost += (shiftMm - maxShiftMm) * 0.5;
        }
    }

    // melyik ujj fogja le a hangot (0 = mutató, 3 = kisujj)
    if (nextPos.GetFretIdx() != 0 && nextHandFret != -1 && nextPos.GetFretIdx() - nextHandFret == 3)
    {
        cost += pinkyPenalty;
    }

    return cost;
}

double Optimization::Urgency(const size_t noteIdx) const
{
    if (noteIdx == 0)
    {
        return 1.0;
    }

    // minél kisebb az idő két hang között, annál nehezebb mozogni, ezért a mozgás költségét felszorozzuk
    const double ioi = notes[noteIdx].GetOnset() - notes[noteIdx - 1].GetOnset();
    return std::clamp(std::sqrt(0.25 / std::max(ioi, 0.03)), 0.6, 4.0);
}

double Optimization::PositionCost(const double currentCenter, const NotePosition &pos, const int handFret) const
{
    double positionCost = 0.0;
    std::vector<int> tuning = FretBoard::GetTuning();
    double centerThreshold = tuning.empty() ? 64.0 : (tuning[0] + 24.0);
    if (currentCenter > centerThreshold && pos.GetFretIdx() < 3)
    {
        positionCost += 5.0; // ha általában magas hangokat játszünk, akkor feljebb legyen lefogás, a lejjebb lefogásokat büntetjük
    }

    if ((pos.GetStringIdx() == 0 || pos.GetStringIdx() == 1) && pos.GetFretIdx() > 12)
    {
        positionCost += 25.0; // az E és A húron ne játszunk riffeket a 12. bund felett
    }

    // vékony húrokat ne játsza üresen riffek közben, kivéve első pozícióban (a kéz az 1-2. bundnál), ott az üres húr természetes
    // ha a kéz pozíciója még nem ismert (-1), büntetünk, különben az üres húrok miatt a kéz sosem kapna pozíciót
    const int highHandFret = 3;
    if (pos.GetFretIdx() == 0 && pos.GetStringIdx() >= 2 && (handFret == -1 || handFret >= highHandFret))
    {
        positionCost += 15.0;
    }

    return positionCost;
}

double Optimization::StringChangeCost(const NotePosition &prevPos, const NotePosition &nextPos) const
{
    const double stringWeight = 10.5; // szomszédos húrra váltás büntetés
    const double skipWeight = 27.5;   // minden átugrott húr büntetése (húrugrás, a pengetőkéznek nehezebb)

    const int stringDiff = abs(prevPos.GetStringIdx() - nextPos.GetStringIdx());
    if (stringDiff == 0)
    {
        return 0.0;
    }
    return stringWeight + skipWeight * (stringDiff - 1);
}

double Optimization::ExtraCost(const NotePosition &nextPos, const NotePosition &prevPos, const NotePosition &prevPrevPos) const
{
    double extraCost = 0.0;

    const int fretDiff = abs(nextPos.GetFretIdx() - prevPos.GetFretIdx());
    if (fretDiff <= 3 && !(prevPos.GetFretIdx() == 0 && nextPos.GetFretIdx() != 0 && abs(nextPos.GetFretIdx() - prevPrevPos.GetFretIdx()) > 4))
    {
         extraCost -= 5.0; // kicsi a bundtávolság jutalom; üres húr után ez az első pozíció közelében tartja a kezet (a kézmodell ezt magától nem tudja)
    }

    bool isPrevPedal = (prevPos.GetFretIdx() == 0 && prevPos.GetStringIdx() <= 1);
    bool isNextPedal = (nextPos.GetFretIdx() == 0 && nextPos.GetStringIdx() <= 1);
    if (isPrevPedal || isNextPedal)
    {
        extraCost -= 5.0; // csak a vastag pedálhúrokat (E és A) jutalmazzuk, ha onnan jövünk vagy oda megyünk
    }

    return extraCost;
}

double Optimization::StepCost(const size_t noteIdx, const double currentCenter, const NotePosition &prevPrevPos, const NotePosition &prevPos, const int prevHandFret, const NotePosition &nextPos, const int nextHandFret) const
{
    double stepCost = HandCost(prevHandFret, nextPos, nextHandFret) * Urgency(noteIdx);
    stepCost += StringChangeCost(prevPos, nextPos);
    stepCost += PositionCost(currentCenter, nextPos, nextHandFret);
    stepCost += ExtraCost(nextPos, prevPos, prevPrevPos);
    return stepCost;
}

std::vector<NotePosition> Optimization::RunOptimization()
{
    std::vector<NotePosition> finalPositions;
    finalPositions.reserve(notes.size());

    std::vector<int> finalHandFrets; // a véglegesített hangokhoz tartozó kézpozíciók
    finalHandFrets.reserve(notes.size());

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
            finalHandFrets.push_back(finalHandFrets.empty() ? -1 : finalHandFrets.back());
            continue;
        }

        double currentCenter = CalculateCenter(i);
        const int lastHandFret = finalHandFrets.empty() ? -1 : finalHandFrets.back();

        for (const auto &pos : firstNotePositions)
        {
            // minden lefogáshoz az összes lehetséges kézpozíciót megvizsgáljuk
            for (const int handFret : PossibleHandFrets(pos, lastHandFret))
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

                    initialCost = StepCost(i, currentCenter, prevPrevPos, prevPos, lastHandFret, pos, handFret);
                }
                Path newPath;
                newPath.positions.push_back(pos);
                newPath.handFrets.push_back(handFret);
                newPath.totalCost = initialCost;
                currentPaths.push_back(newPath);
            }
        }

        for (size_t j = 1; j < window.size(); j++)
        {
            auto nextPositions = FretBoard::GetPositions(window[j].GetMidiNote());
            std::vector<Path> nextPaths;

            double dynamicCenter = CalculateCenter(i + j);

            for (const auto &path : currentPaths)
            {
                const auto &prevPos = path.positions.back();
                const int prevHandFret = path.handFrets.back();

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
                    for (const int nextHandFret : PossibleHandFrets(nextPos, prevHandFret))
                    {
                        const double stepCost = StepCost(i + j, dynamicCenter, prevPrevPos, prevPos, prevHandFret, nextPos, nextHandFret);

                        Path expandedPath = path;
                        expandedPath.positions.push_back(nextPos);
                        expandedPath.handFrets.push_back(nextHandFret);
                        expandedPath.totalCost += stepCost;
                        nextPaths.push_back(expandedPath);
                    }
                }
            }

            // az állapot: előző lefogás, jelenlegi lefogás és a kéz pozíciója
            std::map<std::tuple<int, int, int>, Path> bestStatePaths;

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
                std::tuple<int, int, int> stateKey = {prevId, currId, p.handFrets.back()};

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
        std::vector<int> bestWindowHandFrets;

        for (const auto &path : currentPaths)
        {
            if (path.totalCost < bestCost)
            {
                bestCost = path.totalCost;
                bestWindowPath = path.positions;
                bestWindowHandFrets = path.handFrets;
            }
        }

        if (!bestWindowPath.empty())
        {
            finalPositions.push_back(bestWindowPath[0]);
            finalHandFrets.push_back(bestWindowHandFrets[0]);
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