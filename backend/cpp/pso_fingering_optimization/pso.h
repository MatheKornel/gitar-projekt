#pragma once

#include <vector>
#include "particle.h"
#include "input_notes.h"
#include "note_position.h"

class PSO
{
public:
    PSO(const std::vector<InputNotes> &newNotes, const int newDimension, const int swarmSize);
    std::vector<NotePosition> PsoAlgo(const int stopCondition);

    std::vector<int> g_opt;
    double g_opt_fitness;

private:
    std::vector<Particle> P;
    std::vector<InputNotes> notes;

    int dimension;
    double phi_p = 1.494;
    double phi_g = 1.494;

    void InitializePopulation(const int swarmSize);
    void Evaluation();
    double Fitness(const Particle &particle) const;
    void CalculateVelocity(const double omega);
};