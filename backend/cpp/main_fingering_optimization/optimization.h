#pragma once
#include <vector>
#include "note_position.h"
#include "input_notes.h"

// egy hang egy lehetséges lejátszása: a lefogás és a kéz helyzete (a mutatóujj bundja)
struct HandState
{
    NotePosition pos;
    int handFret = 1;
};

class Optimization
{
public:
    Optimization(const std::vector<InputNotes> &newNotes);
    std::vector<NotePosition> RunOptimization();

private:
    std::vector<InputNotes> notes;
    std::vector<bool> isPedal; // hangonként: pedálhang-e (sokszor ismétlődő legmélyebb vagy legmagasabb hang)

    void FindPedalNotes();
    std::vector<int> PossibleHandFrets(const NotePosition &pos) const;                                         // a kéz lehetséges helyei egy lefogáshoz
    std::vector<HandState> PossibleStates(const size_t noteIdx) const;                                         // a hang összes lefogása az összes kézpozícióval
    double NoteCost(const size_t noteIdx, const HandState &state) const;                                       // egy hang lefogásának költsége
    double FingerCost(const int finger) const;                                                                 // melyik ujj fogja le a hangot
    double TimbreCost(const int stringIdx) const;                                                              // hangszín: a vékonyabb húrok drágábbak
    double NeckCost(const NotePosition &pos) const;                                                            // a húron a kényelmes bundhatár felett
    double TransitionCost(const size_t noteIdx, const HandState &prevState, const HandState &nextState) const; // két egymás utáni hang közötti mozgás
    double StringChangeCost(const NotePosition &prevPos, const NotePosition &nextPos) const;                   // húrváltás (pengetőkéz)
    double HandCost(const int prevHandFret, const int nextHandFret, const double availableTime) const;         // bal kéz mozgása
    double Urgency(const double availableTime) const;                                                          // minél kevesebb idő van a mozgásra, annál nehezebb
    double AvailableTime(const size_t noteIdx, const HandState &nextState) const;                              // mennyi idő jut a kéz mozgására
};
