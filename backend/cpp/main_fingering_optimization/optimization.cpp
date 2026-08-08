#include "optimization.h"
#include "fretboard.h"
#include <iostream>

struct Path
{
    std::vector<NotePosition> positions;
    double totalCost = 0.0;
};

Optimization::Optimization(const std::vector<InputNotes> &newNotes) : notes(std::move(newNotes)) {}

double Optimization::CalculateCenter(const int currentIdx)
{
    const int foresight = 15;
    int count = 0;
    double sumMidi = 0.0;

    for (size_t i = currentIdx; i < currentIdx + foresight && i < notes.size(); i++)
    {
        sumMidi += notes[i].GetMidiNote();
        count++;
    }
    return sumMidi / count;
}

double Optimization::ExtraCost(const double currentCenter, const NotePosition &nextPos, const NotePosition &prevPos) const
{
    double extraCost = 0.0;
    if (currentCenter > 64.0 && nextPos.GetFretIdx() < 5)
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

    return extraCost;
}

std::vector<NotePosition> Optimization::RunOptimization()
{
    std::vector<NotePosition> finalPositions;
    finalPositions.reserve(notes.size());

    const int windowSize = 5;

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

        for (const auto &pos : firstNotePositions)
        {
            double initialCost = 0.0;
            if (!finalPositions.empty())
            {
                initialCost = finalPositions.back().Distance(pos);
            }
            Path newPath;
            newPath.positions.push_back(pos);
            newPath.totalCost = initialCost;
            currentPaths.push_back(newPath);
        }

        double currentCenter = CalculateCenter(i);

        for (size_t j = 1; j < window.size(); j++)
        {
            auto nextPositions = FretBoard::GetPositions(window[j].GetMidiNote());
            std::vector<Path> nextPaths;

            for (const auto &path : currentPaths)
            {
                const auto &prevPos = path.positions.back();

                for (const auto &nextPos : nextPositions)
                {
                    const double stepCost = prevPos.Distance(nextPos);
                    const double extraCost = ExtraCost(currentCenter, nextPos, prevPos);
                    Path expandedPath = path;
                    expandedPath.positions.push_back(nextPos);
                    expandedPath.totalCost += (stepCost + extraCost);
                    nextPaths.push_back(expandedPath);
                }
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