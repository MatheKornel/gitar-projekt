#pragma once

#include <string>

class NotePosition
{
public:
    NotePosition(const int newStringIdx, const int newFretIdx);
    double Distance(const NotePosition &otherPos); // távolság 2 pozíció között
    int GetStringIdx() const;
    int GetFretIdx() const;
    std::string ToString() const;

private:
    int stringIdx; // 0-5 húr
    int fretIdx;   // 0-24 bund
};
