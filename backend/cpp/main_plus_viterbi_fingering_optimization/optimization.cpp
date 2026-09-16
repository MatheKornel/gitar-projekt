#include "optimization.h"
#include "fretboard.h"
#include <iostream>
#include <limits>

Optimization::Optimization(const std::vector<InputNotes> &newNotes) : notes(std::move(newNotes)) {}

double Optimization::CalculateCenter(const size_t currentIdx) const
{
    const size_t foresight = 15;
    int count = 0;
    double sumMidi = 0.0;

    for (size_t i = currentIdx; i < currentIdx + foresight && i < notes.size(); i++)
    {
        sumMidi += notes[i].GetMidiNote();
        count++;
    }
    return sumMidi / count;
}

// 1:1 átvéve az Optimization::ExtraCost-ból - ez a saját, finomított
// ergonómiai/zenei szabályrendszered, most a DP éleinek költségeként használva.
double Optimization::ExtraCost(const double currentCenter, const NotePosition &nextPos, const NotePosition &prevPos) const
{
    double extraCost = 0.0;
    if (currentCenter > 64.0 && nextPos.GetFretIdx() < 5)
    {
        extraCost += 10.0; // ha általában magas hangokat játszunk, akkor feljebb legyen lefogás, a lejjebb lefogásokat büntetjük
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

    // Előre kiszámoljuk minden indexhez a "center" értéket - ez csak az
    // indextől függ, nem az útvonaltól, ezért kívül lehet a DP ciklusán.
    std::vector<double> centers(notes.size());
    for (size_t i = 0; i < notes.size(); i++)
    {
        centers[i] = CalculateCenter(i);
    }

    std::vector<std::vector<double>> minCost(notes.size());
    std::vector<std::vector<int>> parent(notes.size());

    // Első hang: nincs előzmény, tehát nincs mozgási vagy ergonómiai költség sem
    // (a régi Viterbi itt egy mesterséges fretIdx*10 büntetést adott - ez most elmarad,
    // mert nincs jó indoka: az első pozíciót semmi nem indokolja "lentebbre" húzni).
    minCost[0].resize(allPositions[0].size(), 0.0);
    parent[0].resize(allPositions[0].size(), -1);

    for (size_t i = 1; i < notes.size(); i++)
    {
        const size_t currentPositionsCount = allPositions[i].size();
        const size_t prevPositionsCount = allPositions[i - 1].size();

        minCost[i].resize(currentPositionsCount);
        parent[i].resize(currentPositionsCount);

        for (size_t curr = 0; curr < currentPositionsCount; curr++)
        {
            double bestTotalCost = std::numeric_limits<double>::max();
            int bestPrevIdx = -1;

            for (size_t prev = 0; prev < prevPositionsCount; prev++)
            {
                const double stepCost = allPositions[i - 1][prev].Distance(allPositions[i][curr]);
                const double extra = ExtraCost(centers[i], allPositions[i][curr], allPositions[i - 1][prev]);
                const double currentTotalCost = minCost[i - 1][prev] + stepCost + extra;

                if (currentTotalCost < bestTotalCost)
                {
                    bestTotalCost = currentTotalCost;
                    bestPrevIdx = static_cast<int>(prev);
                }
            }
            minCost[i][curr] = bestTotalCost;
            parent[i][curr] = bestPrevIdx;
        }
    }

    std::vector<NotePosition> optimalPositions(notes.size());
    const size_t lastPositionsCount = allPositions[notes.size() - 1].size();
    double minTotal = std::numeric_limits<double>::max();
    int bestLastIdx = 0;

    for (size_t i = 0; i < lastPositionsCount; i++)
    {
        if (minCost[notes.size() - 1][i] < minTotal)
        {
            minTotal = minCost[notes.size() - 1][i];
            bestLastIdx = static_cast<int>(i);
        }
    }

    int currentIdx = bestLastIdx;
    for (int i = static_cast<int>(notes.size()) - 1; i >= 0; i--)
    {
        optimalPositions[i] = allPositions[i][currentIdx];
        if (i > 0)
        {
            currentIdx = parent[i][currentIdx];
        }
    }

    return optimalPositions;
}