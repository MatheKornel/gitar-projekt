#include "fretboard.h"
#include <iostream>

std::vector<std::vector<NotePosition>> FretBoard::GenerateFretBoard()
{
    std::vector<std::vector<NotePosition>> fretboard(89);
    const int openStrings[] = {40, 45, 50, 55, 59, 64};
    const int numStrings = 6;
    const int maxFret = 24;

    for (int stringIdx = 0; stringIdx < numStrings; stringIdx++)
    {
        for (int fretIdx = 0; fretIdx <= maxFret; fretIdx++)
        {
            int midiNote = openStrings[stringIdx] + fretIdx;
            if (midiNote >= 0 && midiNote < fretboard.size())
            {
                fretboard[midiNote].emplace_back(stringIdx, fretIdx);
            }
        }
    }
    return fretboard;
}

const std::vector<NotePosition> FretBoard::GetPositions(const int midiNote)
{
    static const std::vector<std::vector<NotePosition>> fretboard = GenerateFretBoard();
    if (midiNote < 40 || midiNote >= fretboard.size())
    {
        const std::vector<NotePosition> empty;
        std::cerr << "Nincs ilyen MIDI hang: " << midiNote << std::endl;
        return empty;
    }
    return fretboard[midiNote];
}