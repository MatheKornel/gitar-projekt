#include <vector>
#include <string>

class InputNotes
{
public:
    InputNotes(const int newMidiNote, const double newOnset, const double newDuration, const std::string &newNoteName);
    int GetMidiNote() const;
    double GetOnset() const;
    double GetDuration() const;
    std::string GetNoteName() const;
    static const std::vector<InputNotes> LoadNotes(const std::string &filename);

private:
    int midiNote;
    double onset;
    double duration;
    std::string noteName;
};