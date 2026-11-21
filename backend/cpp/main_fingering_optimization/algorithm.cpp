#include "algorithm.h"
#include "optimization.h"

// a saját (végleges) ujjrend optimalizáló bekötése a közös belépési pontba (common/src/app_main.cpp)

std::vector<NotePosition> Optimize(const std::vector<InputNotes> &notes, const bool verbose)
{
    (void)verbose; // ez az eljárás nem ír ki részeredményt
    Optimization opt(notes);
    return opt.RunOptimization();
}

std::string AlgorithmId() { return "main"; }

std::string AlgorithmName() { return "Sajat algoritmus"; }
