#include <iostream>
#include <limits>
#include "viterbi.h"
#include "fretboard.h"

Viterbi::Viterbi(const std::vector<InputNotes> &newNotes) : notes(std::move(newNotes)) {}

std::vector<NotePosition> Viterbi::Optimization()
{
    if (notes.empty())
    {
        std::cout << "Nincsenek hangok!" << std::endl;
        return {};
    }

    std::vector<std::vector<NotePosition>> allPositions(notes.size());
    for (size_t i = 0; i < notes.size(); i++)
    {
        allPositions[i] = FretBoard::GetPositions(notes[i].GetMidiNote());
        if (allPositions[i].empty())
        {
            allPositions[i].emplace_back();
        }
    }

    std::vector<std::vector<double>> minCost(notes.size()); // legkisebb költség egyik hangból a másikba való eljutáshoz (i-edik hang j-edik variációja)
    std::vector<std::vector<int>> parent(notes.size());     // melyik variációból jöttünk, ami ezt a költséget hozta

    // első hang
    minCost[0].resize(allPositions[0].size());
    parent[0].resize(allPositions[0].size());
    for (size_t i = 0; i < allPositions[0].size(); i++)
    {
        const double startCost = allPositions[0][i].GetFretIdx() * 10.0; // minél lejjebb kezdje
        minCost[0][i] = startCost;
        parent[0][i] = -1;
    }

    for (size_t i = 1; i < notes.size(); i++)
    {
        int currentPositionsCount = allPositions[i].size();
        int prevPositionsCount = allPositions[i - 1].size();

        minCost[i].resize(currentPositionsCount);
        parent[i].resize(currentPositionsCount);

        for (size_t curr = 0; curr < currentPositionsCount; curr++)
        {
            double bestTotalCost = DBL_MAX;
            int bestPrevIdx = -1;

            for (size_t prev = 0; prev < prevPositionsCount; prev++)
            {
                double currentTotalCost = minCost[i - 1][prev] + allPositions[i - 1][prev].Distance(allPositions[i][curr]); // előzőig a költség + átmenet költség
                currentTotalCost += allPositions[i][curr].GetFretIdx() * 0.5;                                               // minél lejjebb legyen

                if (currentTotalCost < bestTotalCost)
                {
                    bestTotalCost = currentTotalCost;
                    bestPrevIdx = prev;
                }
            }
            minCost[i][curr] = bestTotalCost;
            parent[i][curr] = bestPrevIdx;
        }
    }

    std::vector<NotePosition> optimalPositions(notes.size());
    const int lastPositionsCount = allPositions[notes.size() - 1].size();
    double min = DBL_MAX;
    int bestLastIdx = 0;

    for (size_t i = 0; i < lastPositionsCount; i++)
    {
        if (minCost[notes.size() - 1][i] < min)
        {
            min = minCost[notes.size() - 1][i];
            bestLastIdx = i;
        }
    }

    int currentIdx = bestLastIdx;
    for (int i = notes.size() - 1; i >= 0; i--)
    {
        optimalPositions[i] = allPositions[i][currentIdx];
        if (i > 0)
        {
            currentIdx = parent[i][currentIdx];
        }
    }

    return optimalPositions;
}