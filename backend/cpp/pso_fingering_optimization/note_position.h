struct NotePosition
{
    int stringIdx; // 0-5
    int fretIdx;   // 0-24

    NotePosition(const int newStringIdx, const int newFretIdx);
    int Distance(const NotePosition &otherPos);
};
