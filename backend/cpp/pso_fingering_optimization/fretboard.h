#include <vector>
#include <memory>
#include "note_position.h"

class FretBoard
{
public:
    static const std::vector<NotePosition> GetPositions(const int midiNote);

private:
    static std::vector<std::vector<NotePosition>> GenerateFretBoard();
};