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
        int lowerFret = std::min(this->fretIdx, otherPos.fretIdx);
        int maxAllowedStretch = 4;

        if (lowerFret >= 7)
            maxAllowedStretch = 5;
        if (lowerFret >= 12)
            maxAllowedStretch = 6;
        if (lowerFret >= 17)
            maxAllowedStretch = 7;

        if (fretDiff > maxAllowedStretch)
        {
            cost += (fretDiff - maxAllowedStretch) * 20.0;
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