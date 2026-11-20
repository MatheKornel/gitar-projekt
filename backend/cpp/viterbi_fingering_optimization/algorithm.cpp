#include "algorithm.h"
#include "viterbi.h"

// a Viterbi ujjrend optimalizáló bekötése a közös belépési pontba (common/src/app_main.cpp)

std::vector<NotePosition> Optimize(const std::vector<InputNotes> &notes, const bool verbose)
{
    (void)verbose; // ez az eljárás nem ír ki részeredményt
    Viterbi viterbi(notes);
    return viterbi.Optimization();
}

std::string AlgorithmId() { return "viterbi"; }

std::string AlgorithmName() { return "Viterbi algoritmus"; }
