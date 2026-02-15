#pragma once

#include <vector>
#include "input_notes.h"

class Particle
{
public:
    Particle(const int newDimension);
    std::vector<int> p;
    std::vector<double> p_velo;
    std::vector<int> p_opt;
    double p_opt_fitness;
    void Initialize(const std::vector<InputNotes> &input); // egy részecske tartalma: az egész szám összes hangjához tartozó random lefogás

private:
    int dimension;
};