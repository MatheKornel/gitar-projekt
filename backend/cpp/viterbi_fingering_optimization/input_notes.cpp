#include "input_notes.h"
#include <fstream>
#include <iostream>

InputNotes::InputNotes(const int newMidiNote, const double newOnset, const double newDuration, const std::string &newNoteName) : midiNote(newMidiNote), onset(newOnset), duration(newDuration), noteName(newNoteName) {}

int InputNotes::GetMidiNote() const { return midiNote; }

double InputNotes::GetOnset() const { return onset; }

double InputNotes::GetDuration() const { return duration; }

std::string InputNotes::GetNoteName() const { return noteName; }

const std::vector<InputNotes> InputNotes::LoadNotes(const std::string &filename)
{
    std::vector<InputNotes> notes;
    std::ifstream inputFile(filename);
    if (!inputFile.is_open())
    {
        std::cerr << "Fajl betoltese sikertelen!" << std::endl;
        return notes;
    }

    int numNotes;
    inputFile >> numNotes;
    notes.reserve(numNotes);

    int midiNote;
    double onset, duration;
    std::string noteName;
    while (inputFile >> midiNote >> onset >> duration >> noteName)
    {
        notes.emplace_back(midiNote, onset, duration, noteName);
    }
    std::cout << "Sikeres fajlbetoltes!" << std::endl;
    return notes;
}