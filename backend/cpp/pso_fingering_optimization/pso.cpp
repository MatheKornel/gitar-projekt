#include "float.h"
#include "pso.h"
#include "random.h"
#include "fretboard.h"
#include <iostream>
#include <cmath>
#include <omp.h>

PSO::PSO(const std::vector<InputNotes> &newNotes, const size_t newDimension, const size_t swarmSize, const int newLimit, const double newImprThreshold)
    : g_opt_fitness(DBL_MAX), notes(newNotes), dimension(newDimension), limit(newLimit), imprThreshold(newImprThreshold)
{
    // a lehetséges lefogásokat egyszer kérjük le, mert a fitnesz függvény nagyon sokszor fut
    positions.resize(notes.size());
    for (size_t j = 0; j < notes.size(); j++)
    {
        positions[j] = FretBoard::GetPositions(notes[j].GetMidiNote());
    }

    g_opt.resize(dimension);
    InitializePopulation(swarmSize);
    Evaluation();
}

bool PSO::StopCondition()
{
    const double improvement = prev_g_opt_fitness - g_opt_fitness;
    if (improvement > imprThreshold)
    {
        stagnationCounter = 0;
        prev_g_opt_fitness = g_opt_fitness;
        return false;
    }
    else
    {
        stagnationCounter++;
        if (stagnationCounter >= limit)
        {
            return true;
        }
        return false;
    }
}

std::vector<NotePosition> PSO::PsoAlgo(const int maxIterations, const int printInterval)
{
    prev_g_opt_fitness = g_opt_fitness;
    stagnationCounter = 0;
    int i = 0;
    double omega = 0.9;
    while (!StopCondition() && i < maxIterations)
    {
        omega = (omega < 0.4) ? 0.4 : omega * 0.995;
        CalculateVelocity(omega);
        for (auto &particle : P)
        {
            for (size_t j = 0; j < dimension; j++)
            {
                const int max = static_cast<int>(positions[j].size());

                // előbb kerekítünk, utána ellenőrizzük a határokat, különben pl. 2.6 -> 3 túlindexelne 3 lefogásnál
                int newPosition = static_cast<int>(std::round(particle.p[j] + particle.p_velo[j]));
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
                particle.p[j] = newPosition;
            }
        }
        Evaluation();
        if (printInterval > 0 && i % printInterval == 0)
        {
            std::cout << "Iteracio: " << i << "\t Legjobb hiba (fitnesz): " << g_opt_fitness << "\n";
        }
        i++;
    }

    std::vector<NotePosition> optimalPositions;
    for (size_t j = 0; j < notes.size(); j++)
    {
        if (positions[j].empty())
        {
            std::cerr << "Nem talalhato lefogas a " << notes[j].GetMidiNote() << " hanghoz!" << std::endl;
            optimalPositions.emplace_back(0, 0);
            continue;
        }
        optimalPositions.emplace_back(positions[j][static_cast<size_t>(g_opt[j])]);
    }
    return optimalPositions;
}

void PSO::InitializePopulation(const size_t swarmSize)
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
#pragma omp parallel for schedule(dynamic)
    for (int i = 0; i < static_cast<int>(P.size()); i++)
    {
        Particle &particle = P[i];
        const double p_fitness = Fitness(particle);
        if (p_fitness < particle.p_opt_fitness)
        {
            particle.p_opt_fitness = p_fitness;
            particle.p_opt = particle.p;
            if (p_fitness < g_opt_fitness)
            {
#pragma omp critical
                {
                    if (p_fitness < g_opt_fitness)
                    {
                        g_opt_fitness = p_fitness;
                        g_opt = particle.p;
                    }
                }
            }
        }
    }
}

double PSO::Fitness(const Particle &particle) const
{
    // érvénytelen lefogás-index esetén nagy büntetés
    for (size_t i = 0; i < notes.size(); i++)
    {
        if (particle.p[i] < 0 || static_cast<size_t>(particle.p[i]) >= positions[i].size())
        {
            return 1000000.0;
        }
    }

    double total = 0;
    const NotePosition startPos = positions[0][static_cast<size_t>(particle.p[0])];

    if (startPos.GetFretIdx() > 4 && startPos.GetFretIdx() != 0)
    {
        total += startPos.GetFretIdx() * 100.0;
    }

    for (size_t i = 0; i + 1 < notes.size(); i++)
    {
        const NotePosition &currentPosition = positions[i][static_cast<size_t>(particle.p[i])];
        const NotePosition &nextPosition = positions[i + 1][static_cast<size_t>(particle.p[i + 1])];
        total += currentPosition.Distance(nextPosition);
        total += currentPosition.GetFretIdx() * 1.5;
    }
    return total;
}

void PSO::CalculateVelocity(const double omega)
{
    // nincs párhuzamosítva: a Random osztály közös generátora nem szálbiztos
    for (int i = 0; i < static_cast<int>(P.size()); i++)
    {
        Particle &particle = P[i];
        for (size_t j = 0; j < dimension; j++)
        {
            const double p_rnd = Random::GetRandomDouble(0.0, 1.0);
            const double g_rnd = Random::GetRandomDouble(0.0, 1.0);

            double momentum = omega * particle.p_velo[j];
            double local_move = phi_p * p_rnd * (particle.p_opt[j] - particle.p[j]);
            double global_move = phi_g * g_rnd * (g_opt[j] - particle.p[j]);

            particle.p_velo[j] = momentum + local_move + global_move;
        }
    }
}
