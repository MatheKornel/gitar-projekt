#include <iostream>
#include "fretboard.h"
#include "input_notes.h"
#include "particle.h"
#include "pso.h"

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
    /*
    for (const auto &note : input)
    {
        std::cout << note.GetNoteName() << "\t" << note.GetMidiNote() << "\t" << note.GetOnset() << "\t" << note.GetDuration() << std::endl;
    }
    */
    /*
    // Particle osztály tesztelése
    Particle p = Particle(input.size());
    p.Initialize(input);
    ;
    */

    PSO pso(std::move(input), input.size(), 50, 10000, 0.0001);
    const auto result = pso.PsoAlgo(5000, 100);
    std::cout << "Fitnesz: " << pso.g_opt_fitness << std::endl;
    std::cout << "Optimalis lefogasok:" << std::endl;
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t" << result[i].ToString() << std::endl;
    }
}