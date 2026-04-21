#pragma once
#include <vector>
#include "note_position.h"
#include "input_notes.h"

class Optimization
{
public:
    Optimization(const std::vector<InputNotes> &newNotes);
    std::vector<NotePosition> RunOptimization();

private:
    std::vector<InputNotes> notes;
};