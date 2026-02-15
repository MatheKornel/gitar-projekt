#include "float.h"
#include "pso.h"
#include "random.h"
#include "fretboard.h"
#include <iostream>

PSO::PSO(const std::vector<InputNotes> &newNotes, const int newDimension, const int swarmSize) : notes(std::move(newNotes)), dimension(newDimension), g_opt_fitness(DBL_MAX)
{
    g_opt.resize(dimension);
    InitializePopulation(swarmSize);
    Evaluation();
}

std::vector<NotePosition> PSO::PsoAlgo(const int stopCondition, const int printInterval)
{
    for (size_t i = 0; i < stopCondition; i++)
    {
        const double omega = 0.9 - (0.5 * i / stopCondition);
        CalculateVelocity(omega);
        for (auto &particle : P)
        {
            for (size_t j = 0; j < dimension; j++)
            {
                double newPosition = particle.p[j] + particle.p_velo[j];
                const int max = FretBoard::GetPositions(notes[j].GetMidiNote()).size();
                if (newPosition >= max)
                {
                    newPosition = max - 1;
                    particle.p_velo[j] = 0;
                }
                else if (newPosition < 0)
                {
                    newPosition = 0;
                    particle.p_velo[j] = 0;
                }
                particle.p[j] = static_cast<int>(std::round(newPosition));
            }
        }
        Evaluation();
        if (i % printInterval == 0)
        {
            std::cout << "Iteracio: " << i << "\t Legjobb hiba (fitnesz): " << g_opt_fitness << "\n";
        }
    }
    std::vector<NotePosition> optimalPositions;
    for (size_t i = 0; i < notes.size(); i++)
    {
        optimalPositions.emplace_back(FretBoard::GetPositions(notes[i].GetMidiNote())[g_opt[i]]);
    }
    return optimalPositions;
}

void PSO::InitializePopulation(const int swarmSize)
{
    for (size_t i = 0; i < swarmSize; i++)
    {
        Particle particle(dimension);
        particle.Initialize(notes);
        const double p_fitness = Fitness(particle);
        particle.p_opt_fitness = p_fitness;
        if (p_fitness < g_opt_fitness)
        {
            g_opt_fitness = p_fitness;
            g_opt = particle.p_opt;
        }

        P.emplace_back(std::move(particle));
    }
}

void PSO::Evaluation()
{
    for (auto &particle : P)
    {
        const double p_fitness = Fitness(particle);
        if (p_fitness < particle.p_opt_fitness)
        {
            particle.p_opt_fitness = p_fitness;
            particle.p_opt = particle.p;
            if (p_fitness < g_opt_fitness)
            {
                g_opt_fitness = p_fitness;
                g_opt = particle.p;
            }
        }
    }
}

double PSO::Fitness(const Particle &particle) const
{
    double total = 0;
    for (size_t i = 0; i < notes.size() - 1; i++)
    {
        const int currentNoteIdx = particle.p[i];
        const int nextNoteIdx = particle.p[i + 1];
        const auto &pos1 = FretBoard::GetPositions(notes[i].GetMidiNote());
        const auto &pos2 = FretBoard::GetPositions(notes[i + 1].GetMidiNote());

        if (currentNoteIdx >= pos1.size() || nextNoteIdx >= pos2.size())
        {
            return 1000000.0;
        }

        NotePosition currentPosition = pos1[currentNoteIdx];
        NotePosition nextPosition = pos2[nextNoteIdx];
        total += currentPosition.Distance(nextPosition);
        total += currentPosition.GetFretIdx() * 0.5;
    }
    return total;
}

void PSO::CalculateVelocity(const double omega)
{
    for (auto &particle : P)
    {
        for (size_t i = 0; i < dimension; i++)
        {
            const double p_rnd = Random::GetRandomDouble(0.0, 1.0);
            const double g_rnd = Random::GetRandomDouble(0.0, 1.0);

            double momentum = omega * particle.p_velo[i];
            double local_move = phi_p * p_rnd * (particle.p_opt[i] - particle.p[i]);
            double global_move = phi_g * g_rnd * (g_opt[i] - particle.p[i]);

            particle.p_velo[i] = momentum + local_move + global_move;
        }
    }
}