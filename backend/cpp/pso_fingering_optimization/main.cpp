#include <iostream>
#include "fretboard.h"

int main()
{
    auto positon = FretBoard::GetPositions(56);
    for (const auto &pos : positon)
    {
        std::cout << "Hur: " << pos.stringIdx << "\tBund: " << pos.fretIdx << std::endl;
    }
}