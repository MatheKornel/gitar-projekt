#include <iostream>
#include "fretboard.h"
#include "input_notes.h"

int main()
{
    const auto input = InputNotes::LoadNotes("notes.txt");
    for (const auto &note : input)
    {
        std::cout << note.GetNoteName() << "\t" << note.GetMidiNote() << "\n";
    }
}