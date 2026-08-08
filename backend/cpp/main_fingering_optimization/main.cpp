#include <iostream>
#include <string>
#include "fretboard.h"
#include "input_notes.h"
#include "optimization.h"

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        std::cerr << "Hiba: Nem adtad meg a bemeneti fajl nevet paramaterkent!" << std::endl;
        return 1;
    }

    std::string filePath = argv[1];

    const auto input = InputNotes::LoadNotes(filePath);

    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));
    const auto result = Optimization(input).RunOptimization();
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }

    return 0;
}