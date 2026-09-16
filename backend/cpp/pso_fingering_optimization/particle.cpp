#include "particle.h"
#include "float.h"
#include "random.h"
#include "input_notes.h"
#include "fretboard.h"

Particle::Particle(const size_t newDimension) : p_opt_fitness(DBL_MAX), dimension(newDimension)
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
        const int maxIdx = position.empty() ? 0 : static_cast<int>(position.size()) - 1;
        p[i] = Random::GetRandomInt(0, maxIdx);
        p_velo[i] = Random::GetRandomDouble(0.0, 1.0);
        p_opt[i] = p[i];
    }
}