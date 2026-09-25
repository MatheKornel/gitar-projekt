#include "note_position.h"
#include <unordered_map>

NotePosition::NotePosition(const int newStringIdx, const int newFretIdx) : stringIdx(newStringIdx), fretIdx(newFretIdx) {}

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