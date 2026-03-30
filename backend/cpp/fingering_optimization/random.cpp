#include <random>
#include "random.h"

int Random::GetRandomInt(const int min, const int max)
{
    static std::mt19937 gen(std::random_device{}());
    static std::uniform_int_distribution<int> dis(min, max);
    return dis(gen);
}

double Random::GetRandomDouble(const double min, const double max)
{
    static std::mt19937 gen(std::random_device{}());
    static std::uniform_real_distribution<double> dis(min, max);
    return dis(gen);
}