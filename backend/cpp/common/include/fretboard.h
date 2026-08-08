#pragma once

#include <vector>
#include <memory>
#include "note_position.h"

class FretBoard
{
public:
    static const std::vector<NotePosition> GetPositions(const int midiNote); // visszaadja egy MIDI hanghoz tartozó lehetséges lefogásokat
    static void SetTuning(const std::vector<int> &newOpenStrings);           // a 6 üres húr MIDI hangmagasságának beállítása, a GetPositions első hívása előtt kell meghívni

private:
    static std::vector<std::vector<NotePosition>> GenerateFretBoard(); // legenerálja a hangokhoz tartozó lefogási pontokat
    static std::vector<int> openStrings;                               // a 6 üres húr MIDI hangmagassága, alapértelmezetten standard EADGBE
};