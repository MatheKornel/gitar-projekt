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
    double CalculateCenter(const size_t currentIdx);
    double InitialFretPenalty(const NotePosition& pos) const;
    double Urgency(const size_t noteIdx) const;
    std::vector<int> PossibleHandFrets(const NotePosition &pos, const int prevHandFret) const;
    double HandCost(const int prevHandFret, const NotePosition &nextPos, const int nextHandFret) const; // bal kéz mozgása
    double StringChangeCost(const NotePosition &prevPos, const NotePosition &nextPos) const;          // húrváltás (pengetőkéz)
    double PositionCost(const double currentCenter, const NotePosition &pos) const;                  // a lefogás helye a fogólapon
    double ExtraCost(const NotePosition &nextPos, const NotePosition &prevPos, const NotePosition &prevPrevPos) const;
    double StepCost(const size_t noteIdx, const double currentCenter, const NotePosition &prevPrevPos, const NotePosition &prevPos, const int prevHandFret, const NotePosition &nextPos, const int nextHandFret) const;
};