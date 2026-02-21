#pragma once
#include <vector>
#include "input_notes.h"
#include "note_position.h"

class Viterbi
{
public:
    Viterbi(const std::vector<InputNotes> &newNotes);
    std::vector<NotePosition> Optimization();

private:
    std::vector<InputNotes> notes;
};