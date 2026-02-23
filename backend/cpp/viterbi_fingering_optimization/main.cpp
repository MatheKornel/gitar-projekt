#include <iostream>
#include "fretboard.h"
#include "input_notes.h"
#include "viterbi.h"

int main()
{
    const auto input = InputNotes::LoadNotes("notes.txt");
    /*
    for (const auto &note : input)
    {
        std::cout << note.GetNoteName() << "\t" << note.GetMidiNote() << std::endl;
    }
    */

    const auto result = Viterbi(input).Optimization();
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }
}