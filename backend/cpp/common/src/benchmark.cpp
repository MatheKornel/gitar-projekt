#include "benchmark.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>

BenchmarkCase Benchmark::LoadFromFile(const std::string &filepath, const std::string &testName)
{
    BenchmarkCase bc;
    bc.testName = testName;
    bc.tuning = {40, 45, 50, 55, 59, 64}; // standard E hangolás, ha a fájl nem ad meg mást
    std::ifstream file(filepath);

    if (!file.is_open())
    {
        std::cerr << "[!] Hiba a benchmark fajl megnyitasakor: " << filepath << "\n";
        return bc;
    }

    std::string line;
    int lineNumber = 0;
    while (std::getline(file, line))
    {
        lineNumber++;

        // windowsos sorvégek levágása
        if (!line.empty() && line.back() == '\r')
            line.pop_back();

        // hangolás sor, pl: "# tuning: 40 45 50 55 59 64"
        const std::string tuningPrefix = "# tuning:";
        if (line.rfind(tuningPrefix, 0) == 0)
        {
            std::istringstream tuningStream(line.substr(tuningPrefix.size()));
            std::vector<int> tuning;
            int openString;
            while (tuningStream >> openString)
            {
                tuning.push_back(openString);
            }

            if (tuning.size() == 6)
                bc.tuning = tuning;
            else
                std::cerr << "[!] " << testName << " " << lineNumber << ". sor: a hangolasnak 6 szambol kell allnia, a standard E marad\n";
            continue;
        }

        // üres sor, megjegyzés vagy fejléc
        if (line.empty() || line[0] == '#' || line.rfind("MIDI", 0) == 0)
            continue;

        std::istringstream iss(line);
        int midi;
        double onset, duration;
        std::string name, positionsText;

        if (!(iss >> midi >> onset >> duration >> name >> positionsText))
        {
            std::cerr << "[!] " << testName << " " << lineNumber << ". sor nem ertelmezheto, kimarad: " << line << "\n";
            continue;
        }

        std::vector<std::pair<int, int>> positions = ParsePositions(positionsText);
        if (positions.empty())
        {
            std::cerr << "[!] " << testName << " " << lineNumber << ". sor: hibas lefogas formatum (pl. 3:12 vagy 3:12|4:8 kell), kimarad: " << positionsText << "\n";
            continue;
        }

        bc.inputNotes.push_back(InputNotes(midi, onset, duration, name));
        bc.acceptedPositions.push_back(positions);
    }

    ValidatePositions(bc);
    return bc;
}

std::vector<std::pair<int, int>> Benchmark::ParsePositions(const std::string &text)
{
    std::vector<std::pair<int, int>> positions;
    std::istringstream textStream(text);
    std::string part;

    // a lefogásokat a | jel választja el
    while (std::getline(textStream, part, '|'))
    {
        std::istringstream partStream(part);
        int stringIdx, fretIdx;
        char separator;

        // egy lefogás "húr:bund" alakú
        if (!(partStream >> stringIdx >> separator >> fretIdx) || separator != ':')
        {
            return {};
        }
        positions.push_back({stringIdx, fretIdx});
    }
    return positions;
}

void Benchmark::ValidatePositions(const BenchmarkCase &testCase)
{
    for (size_t i = 0; i < testCase.acceptedPositions.size(); i++)
    {
        for (const auto &pos : testCase.acceptedPositions[i])
        {
            const int stringIdx = pos.first;
            const int fretIdx = pos.second;

            if (stringIdx < 0 || stringIdx > 5 || fretIdx < 0 || fretIdx > 24)
            {
                std::cerr << "[!] " << testCase.testName << " " << (i + 1) << ". hang (" << testCase.inputNotes[i].GetNoteName()
                          << "): nem letezo lefogas " << stringIdx << ":" << fretIdx << "\n";
            }
            else if (testCase.tuning[stringIdx] + fretIdx != testCase.inputNotes[i].GetMidiNote())
            {
                std::cerr << "[!] " << testCase.testName << " " << (i + 1) << ". hang (" << testCase.inputNotes[i].GetNoteName()
                          << ", MIDI " << testCase.inputNotes[i].GetMidiNote() << "): a " << stringIdx << ":" << fretIdx
                          << " lefogas MIDI " << testCase.tuning[stringIdx] + fretIdx << " hangot adna\n";
            }
        }
    }
}

std::string Benchmark::PositionsToString(const std::vector<std::pair<int, int>> &positions)
{
    std::string text;
    for (size_t i = 0; i < positions.size(); i++)
    {
        if (i > 0)
            text += " | ";
        text += std::to_string(positions[i].first) + ":" + std::to_string(positions[i].second);
    }
    return text;
}

BenchmarkResult Benchmark::Evaluate(const BenchmarkCase &testCase, const std::vector<std::pair<int, int>> &actualPositions, std::ofstream &logFile)
{
    logFile << "Futtatas: [" << testCase.testName << "]\n";

    BenchmarkResult result;
    result.total = static_cast<int>(testCase.acceptedPositions.size());

    if (actualPositions.size() != testCase.acceptedPositions.size())
    {
        logFile << "  [!] HIBA: Kimenet merete nem egyezik! Vart: " << result.total << ", Kapott: " << actualPositions.size() << "\n\n";
        return result;
    }

    for (size_t i = 0; i < testCase.acceptedPositions.size(); i++)
    {
        const auto &accepted = testCase.acceptedPositions[i];
        const auto &actual = actualPositions[i];

        // megkeressük, hányadik elfogadható lefogás egyezik a kapottal (-1, ha egyik sem)
        int matchIdx = -1;
        for (size_t k = 0; k < accepted.size(); k++)
        {
            if (accepted[k] == actual)
            {
                matchIdx = static_cast<int>(k);
                break;
            }
        }

        const std::string actualText = std::to_string(actual.first) + ":" + std::to_string(actual.second);

        if (matchIdx == 0)
        {
            result.preferredCorrect++;
            result.acceptedCorrect++;
        }
        else if (matchIdx > 0)
        {
            result.acceptedCorrect++;
            logFile << "  ~ Alternativ lefogas a(z) " << (i + 1) << ". hangnal (" << testCase.inputNotes[i].GetNoteName() << "): "
                    << "Kedvenc -> " << accepted[0].first << ":" << accepted[0].second << " | Kapott -> " << actualText << "\n";
        }
        else
        {
            logFile << "  - Hiba a(z) " << (i + 1) << ". hangnal (" << testCase.inputNotes[i].GetNoteName() << "): "
                    << "Vart -> " << PositionsToString(accepted) << " | Kapott -> " << actualText << "\n";
        }
    }

    const double preferredAccuracy = (static_cast<double>(result.preferredCorrect) / result.total) * 100.0;
    const double acceptedAccuracy = (static_cast<double>(result.acceptedCorrect) / result.total) * 100.0;

    logFile << std::fixed << std::setprecision(1)
            << "  Eredmeny: kedvenc " << result.preferredCorrect << "/" << result.total << " (" << preferredAccuracy << "%), "
            << "elfogadhato " << result.acceptedCorrect << "/" << result.total << " (" << acceptedAccuracy << "%)\n\n";

    return result;
}
