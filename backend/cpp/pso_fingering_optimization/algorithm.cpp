#include <iostream>
#include "algorithm.h"
#include "pso.h"

// a PSO ujjrend optimalizáló bekötése a közös belépési pontba (common/src/app_main.cpp)

// PSO paraméterek
const size_t swarmSize = 50;                // részecskék száma
const int stagnationLimit = 10000;          // ennyi javulás nélküli iteráció után leáll
const double improvementThreshold = 0.0001; // ennél kisebb javulás nem számít javulásnak
const int maxIterations = 5000;             // legfeljebb ennyi iteráció
const int printInterval = 100;              // fájlos futtatásnál ennyi iterációnként kiírja a legjobb fitneszt

std::vector<NotePosition> Optimize(const std::vector<InputNotes> &notes, const bool verbose)
{
    PSO pso(notes, notes.size(), swarmSize, stagnationLimit, improvementThreshold);
    const auto result = pso.PsoAlgo(maxIterations, verbose ? printInterval : 0);

    if (verbose)
    {
        std::cout << "Fitnesz: " << pso.g_opt_fitness << std::endl;
        std::cout << "Optimalis lefogasok:" << std::endl;
    }
    return result;
}

std::string AlgorithmId() { return "pso"; }

std::string AlgorithmName() { return "PSO algoritmus"; }
