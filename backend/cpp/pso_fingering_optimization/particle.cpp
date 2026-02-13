#include "particle.h"
#include "float.h"
#include "random.h"
#include "input_notes.h"
#include "fretboard.h"

Particle::Particle(const int newDimension) : dimension(newDimension), p_opt_fitness(DBL_MAX)
{
    p.resize(dimension);
    p_velo.resize(dimension);
    p_opt.resize(dimension);
}

void Particle::Initialize(const std::vector<InputNotes> &input)
{
    for (size_t i = 0; i < dimension; i++)
    {
        const auto &position = FretBoard::GetPositions(input[i].GetMidiNote());
        p[i] = Random::GetRandomInt(0, position.size() - 1);
        p_velo[i] = Random::GetRandomDouble(0.0, 1.0);
        p_opt[i] = p[i];
    }
}