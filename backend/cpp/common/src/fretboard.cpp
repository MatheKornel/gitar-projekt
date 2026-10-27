#include "fretboard.h"
#include <iostream>

std::vector<int> FretBoard::openStrings = {40, 45, 50, 55, 59, 64};
std::vector<std::vector<NotePosition>> FretBoard::fretboard;

void FretBoard::SetTuning(const std::vector<int> &newOpenStrings)
{
    if (newOpenStrings.size() != 6)
    {
        std::cerr << "Ervenytelen hangolas (6 hurnak kell lennie), a jelenlegi hangolas marad ervenyben." << std::endl;
        return;
    }
    openStrings = newOpenStrings;
    fretboard = GenerateFretBoard(); // új hangolásnál a lefogások is megváltoznak
}

std::vector<std::vector<NotePosition>> FretBoard::GenerateFretBoard()
{
    std::vector<std::vector<NotePosition>> fretboard(89);
    const int numStrings = 6;
    const int maxFret = 24;

    for (int stringIdx = 0; stringIdx < numStrings; stringIdx++)
    {
        for (int fretIdx = 0; fretIdx <= maxFret; fretIdx++)
        {
            int midiNote = openStrings[stringIdx] + fretIdx;
            if (midiNote >= 0 && static_cast<size_t>(midiNote) < fretboard.size())
            {
                fretboard[midiNote].emplace_back(stringIdx, fretIdx);
            }
        }
    }
    return fretboard;
}

const std::vector<NotePosition> FretBoard::GetPositions(const int midiNote)
{
    if (fretboard.empty())
    {
        fretboard = GenerateFretBoard();
    }

    if (midiNote < 0 || static_cast<size_t>(midiNote) >= fretboard.size())
    {
        const std::vector<NotePosition> empty;
        std::cerr << "Nincs ilyen MIDI hang: " << midiNote << std::endl;
        return empty;
    }
    return fretboard[midiNote];
}

std::vector<int> FretBoard::GetTuning() { return openStrings; }