#pragma once

#include <vector>
#include "particle.h"
#include "input_notes.h"
#include "note_position.h"

class PSO
{
public:
    PSO(const std::vector<InputNotes> &newNotes, const size_t newDimension, const size_t swarmSize, const int newLimit, const double newImprThreshold);
    std::vector<NotePosition> PsoAlgo(const int stopCondition, const int printInterval);

    std::vector<int> g_opt;
    double g_opt_fitness;

private:
    std::vector<Particle> P;
    std::vector<InputNotes> notes;

    size_t dimension;
    double phi_p = 2.0;
    double phi_g = 1.0;

    double prev_g_opt_fitness;
    int stagnationCounter;
    int limit;
    double imprThreshold;

    void InitializePopulation(const size_t swarmSize);
    void Evaluation();
    double Fitness(const Particle &particle) const;
    void CalculateVelocity(const double omega);
    bool StopCondition();
};