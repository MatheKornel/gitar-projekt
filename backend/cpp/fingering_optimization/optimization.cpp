#include "optimization.h"
#include "fretboard.h"
#include <iostream>

Optimization::Optimization(const std::vector<InputNotes> &newNotes) : notes(std::move(newNotes)) {}

std::vector<NotePosition> Optimization::RunOptimization()
{
    if (notes.empty())
    {
        std::cout << "Nincsenek hangok!" << std::endl;
        return {};
    }
}