#pragma once

#include <vector>
#include <memory>
#include "note_position.h"

class FretBoard
{
public:
    static const std::vector<NotePosition> GetPositions(const int midiNote); // visszaadja egy MIDI hanghoz tartozó lehetséges lefogásokat

private:
    static std::vector<std::vector<NotePosition>> GenerateFretBoard(); // legenerálja a hangokhoz tartozó lefogási pontokat
};