#include <iostream>
#include "fretboard.h"
#include "input_notes.h"
#include "particle.h"

int main()
{
    /*
    // Gitár nyak generálás és abban keresés tesztelése
    auto positon = FretBoard::GetPositions(60);
    for (const auto &pos : positon)
    {
        std::cout << "Hur: " << pos.GetStringIdx() << "\tBund: " << pos.GetFretIdx() << std::endl;
    }
    */

    // Fájl betöltés tesztelése
    const auto input = InputNotes::LoadNotes("notes.txt");
    for (const auto &note : input)
    {
        std::cout << note.GetNoteName() << "\t" << note.GetMidiNote() << "\t" << note.GetOnset() << "\t" << note.GetDuration() << std::endl;
    }

    // Particle osztály tesztelése
    Particle p = Particle(input.size());
    p.Initialize(input);
    ;
}