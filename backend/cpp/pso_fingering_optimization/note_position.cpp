#include "note_position.h"
#include <cmath>

NotePosition::NotePosition(const int newStringIdx, const int newFretIdx) : stringIdx(newStringIdx), fretIdx(newFretIdx) {}

int NotePosition::Distance(const NotePosition &otherPos)
{
    return abs(this->stringIdx - otherPos.stringIdx) + abs(this->fretIdx - otherPos.fretIdx);
}

int NotePosition::GetStringIdx() const { return stringIdx; }

int NotePosition::GetFretIdx() const { return fretIdx; }

std::string NotePosition::ToString() const
{
    return "Hur: " + std::to_string(stringIdx) + "\tBund: " + std::to_string(fretIdx);
}