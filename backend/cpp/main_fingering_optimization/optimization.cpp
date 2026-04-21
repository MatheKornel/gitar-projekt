#include "optimization.h"
#include "fretboard.h"
#include <iostream>

struct Path
{
    std::vector<NotePosition> positions;
    double totalCost = 0.0;
};

Optimization::Optimization(const std::vector<InputNotes> &newNotes) : notes(std::move(newNotes)) {}

std::vector<NotePosition> Optimization::RunOptimization()
{
    std::vector<NotePosition> finalPositions;
    finalPositions.reserve(notes.size());

    const int WINDOW_SIZE = 5;

    for (size_t i = 0; i < notes.size(); i++)
    {
        std::vector<InputNotes> window;
        for (size_t j = i; j < i + WINDOW_SIZE && j < notes.size(); j++)
        {
            window.push_back(notes[j]);
        }

        std::vector<Path> currentPaths;
        auto firstNotePositions = FretBoard::GetPositions(window[0].GetMidiNote());

        if (firstNotePositions.empty())
        {
            std::cerr << "Nem található lefogás a " << window[0].GetMidiNote() << " hanghoz!" << std::endl;
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

        for (size_t j = 1; j < window.size(); j++)
        {
            auto nextPositions = FretBoard::GetPositions(window[j].GetMidiNote());
            std::vector<Path> nextPaths;

            for (auto &path : currentPaths)
            {
                for (const auto &nextPos : nextPositions)
                {
                    double stepCost = path.positions.back().Distance(nextPos);
                    Path expandedPath = path;
                    expandedPath.positions.push_back(nextPos);
                    expandedPath.totalCost += stepCost;
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
    }

    return finalPositions;
}