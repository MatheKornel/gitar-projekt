#include "note_position.h"
#include <cmath>

NotePosition::NotePosition(const int newStringIdx, const int newFretIdx) : stringIdx(newStringIdx), fretIdx(newFretIdx) {}

double NotePosition::Distance(const NotePosition &otherPos)
{
    const bool isOpenString = (this->fretIdx == 0 || otherPos.fretIdx == 0);
    const int stringDiff = abs(this->stringIdx - otherPos.stringIdx);
    const int fretDiff = abs(this->fretIdx - otherPos.fretIdx);

    if (stringDiff == 0 && fretDiff == 0)
    {
        return 0.0;
    }

    const double stringWeight = 2.5;                    // húrváltás büntetés
    const double fretWeight = isOpenString ? 1.5 : 5.0; // bundváltás büntetés

    double cost = (stringWeight * stringDiff) + (fretWeight * fretDiff);

    if (!isOpenString && fretDiff > 4)
    {
        cost += (fretDiff - 4) * 20.0;
    }

    /*
    if (stringDiff > 0 && fretDiff < 5 && !isOpenString)
    {
        cost += 20.0;
    }
    */

    return cost;
}

int NotePosition::GetStringIdx() const { return stringIdx; }

int NotePosition::GetFretIdx() const { return fretIdx; }

std::string NotePosition::ToString() const
{
    return "Hur: " + std::to_string(stringIdx) + "\tBund: " + std::to_string(fretIdx);
}