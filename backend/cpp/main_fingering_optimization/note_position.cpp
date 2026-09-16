#include "note_position.h"
#include <cmath>
#include <unordered_map>
#include <algorithm>

NotePosition::NotePosition(const int newStringIdx, const int newFretIdx) : stringIdx(newStringIdx), fretIdx(newFretIdx) {}

double NotePosition::Distance(const NotePosition &otherPos) const
{
    const bool isOpenString = (this->fretIdx == 0 || otherPos.fretIdx == 0);
    const int stringDiff = abs(this->stringIdx - otherPos.stringIdx);
    const int fretDiff = abs(this->fretIdx - otherPos.fretIdx);

    if (stringDiff == 0 && fretDiff == 0)
    {
        return 0.0;
    }

    const double stringWeight = 2.5;                    // húrváltás büntetés
    const double fretWeight = isOpenString ? 3.0 : 5.0; // bundváltás büntetés

    double cost = (stringWeight * stringDiff) + (fretWeight * fretDiff);

    if (!isOpenString)
    {
        // menzúra mm-ben (a 648 mm a tipikus gitár menzúra)
        const double L = 648.0; 
        
        // bundok fizikai távolsága a nyeregtől (mm)
        double currentFretMm = L * (1.0 - std::pow(2.0, -this->fretIdx / 12.0));
        double otherFretMm = L * (1.0 - std::pow(2.0, -otherPos.fretIdx / 12.0));
        
        // két bund közötti távolság mm-ben
        double spanMm = std::abs(currentFretMm - otherFretMm);
        
        // kb 100 mm a kényelmes határ
        const double maxHandSpanMm = 100.0; 
        
        // ha a fizikai távolság meghaladja a kéz fesztávját, mm-ként büntetjük
        if (spanMm > maxHandSpanMm)
        {
            cost += (spanMm - maxHandSpanMm) * 0.5;
        }
    }

    return cost;
}

int NotePosition::GetStringIdx() const { return stringIdx; }

int NotePosition::GetFretIdx() const { return fretIdx; }

std::string NotePosition::ToString() const
{
    static const std::unordered_map<int, std::string> stringNames = {
        {0, "E"},
        {1, "A"},
        {2, "D"},
        {3, "G"},
        {4, "B"},
        {5, "e"}};

    return "Hur: " + stringNames.at(stringIdx) + "\tBund: " + std::to_string(fretIdx);
}