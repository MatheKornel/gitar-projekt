#include <vector>
#include <memory>
#include "note_position.h"

struct FretBoard
{
    std::vector<std::vector<NotePosition>> GenerateFretBoard();
};