#include <iostream>
#include <string>
#include "fretboard.h"
#include "input_notes.h"
#include "optimization.h"

int main()
{
    const auto input = InputNotes::LoadNotes("notes.txt");

    const auto result = Optimization(input).RunOptimization();
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }
}