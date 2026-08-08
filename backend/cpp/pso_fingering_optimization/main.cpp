#include <iostream>
#include "fretboard.h"
#include "input_notes.h"
#include "particle.h"
#include "pso.h"

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        std::cerr << "Hiba: Nem adtad meg a bemeneti fajl nevet paramaterkent!" << std::endl;
        return 1;
    }

    std::string filePath = argv[1];

    const auto input = InputNotes::LoadNotes("notes.txt");

    PSO pso(std::move(input), input.size(), 50, 10000, 0.0001);
    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));
    const auto result = pso.PsoAlgo(5000, 100);
    std::cout << "Fitnesz: " << pso.g_opt_fitness << std::endl;
    std::cout << "Optimalis lefogasok:" << std::endl;
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t" << result[i].ToString() << std::endl;
    }
}