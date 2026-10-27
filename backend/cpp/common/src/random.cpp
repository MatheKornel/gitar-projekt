#include <random>
#include "random.h"

// a generátor egyszer jön létre, de az eloszlást minden hívásnál az aktuális határokkal hozzuk létre
// (static eloszlás esetén az első hívás határai maradnának érvényben minden további hívásnál)
static std::mt19937 &Generator()
{
    static std::mt19937 gen(std::random_device{}());
    return gen;
}

int Random::GetRandomInt(const int min, const int max)
{
    std::uniform_int_distribution<int> dis(min, max);
    return dis(Generator());
}

double Random::GetRandomDouble(const double min, const double max)
{
    std::uniform_real_distribution<double> dis(min, max);
    return dis(Generator());
}
