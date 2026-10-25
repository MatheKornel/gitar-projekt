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

std::vector<BenchmarkCase> Benchmark::LoadAllCases(const std::string &benchmarkDir)
{
    // a tesztek nevei, a fájlnév: <név>_fing-opt_test.txt
    const std::vector<std::string> testNames = {
        "jotun_clean",
        "almost_honest_clean",
        "ashes_in_your_mouth_clean",
        "AR_Lick1_FN",
        "AR_Lick3_FN",
        "breaking_the_law_clean",
        "A_0-3-5-3-0",
        "A_clean",
        "E_0-3-5-3-0",
        "e0_clean",
        "e24_clean",
        "endgame_clean",
        "trust_clean",
        "powerslave_clean",
        "family_tree_clean_D#",
        "deja_vu_intro_clean",
        "deja_vu_main_clean",
        "never_walk_alone_clean",
        "stranger_in_a_strange_land_clean",
        "the_loneliness_of_the_long_distance_runner_clean"};

    std::vector<BenchmarkCase> tests;
    for (const auto &testName : testNames)
    {
        tests.push_back(LoadFromFile(benchmarkDir + "/" + testName + "_fing-opt_test.txt", testName));
    }
    return tests;
}

void BenchmarkSummary::Add(const BenchmarkResult &result)
{
    if (result.total == 0)
        return;

    validTests++;
    sumPreferredAccuracy += (static_cast<double>(result.preferredCorrect) / result.total) * 100.0;
    sumAcceptedAccuracy += (static_cast<double>(result.acceptedCorrect) / result.total) * 100.0;
    totalNotes += result.total;
    totalPreferredCorrect += result.preferredCorrect;
    totalAcceptedCorrect += result.acceptedCorrect;
    totalChoiceNotes += result.choiceTotal;
    totalChoicePreferredCorrect += result.choicePreferredCorrect;
    totalChoiceAcceptedCorrect += result.choiceAcceptedCorrect;
}

void BenchmarkSummary::Print(std::ofstream &logFile, const std::string &algoName) const
{
    if (validTests == 0)
    {
        std::cout << "Nem futott le egyetlen teszt sem.\n";
        return;
    }

    const double preferredTestAccuracy = sumPreferredAccuracy / validTests;
    const double acceptedTestAccuracy = sumAcceptedAccuracy / validTests;
    const double preferredNoteAccuracy = (static_cast<double>(totalPreferredCorrect) / totalNotes) * 100.0;
    const double acceptedNoteAccuracy = (static_cast<double>(totalAcceptedCorrect) / totalNotes) * 100.0;

    logFile << std::fixed << std::setprecision(1);
    logFile << "=======================================\n";
    logFile << "VEGSO EREDMENYEK - " << algoName << " (" << validTests << " teszt, " << totalNotes << " hang):\n";
    logFile << "Kedvenc lefogas:\n";
    logFile << "  Teszt-alapu (Sulyozatlan) pontossag: " << preferredTestAccuracy << "%\n";
    logFile << "  Hang-alapu (Sulyozott) pontossag:    " << preferredNoteAccuracy << "% (" << totalPreferredCorrect << "/" << totalNotes << ")\n";
    logFile << "Elfogadhato lefogas:\n";
    logFile << "  Teszt-alapu (Sulyozatlan) pontossag: " << acceptedTestAccuracy << "%\n";
    logFile << "  Hang-alapu (Sulyozott) pontossag:    " << acceptedNoteAccuracy << "% (" << totalAcceptedCorrect << "/" << totalNotes << ")\n";

    std::cout << std::fixed << std::setprecision(1);
    std::cout << "Kedvenc lefogas     - teszt-alapu: " << preferredTestAccuracy << "%, hang-alapu: " << preferredNoteAccuracy << "%\n";
    std::cout << "Elfogadhato lefogas - teszt-alapu: " << acceptedTestAccuracy << "%, hang-alapu: " << acceptedNoteAccuracy << "%\n";

    // választásos hangokon csak hang-alapú pontosságot számolunk (van teszt, amiben egy választásos hang sincs)
    if (totalChoiceNotes > 0)
    {
        const double choicePreferredAccuracy = (static_cast<double>(totalChoicePreferredCorrect) / totalChoiceNotes) * 100.0;
        const double choiceAcceptedAccuracy = (static_cast<double>(totalChoiceAcceptedCorrect) / totalChoiceNotes) * 100.0;

        logFile << "Valasztasos hangokon (" << totalChoiceNotes << " hang, hang-alapu):\n";
        logFile << "  Kedvenc lefogas:     " << choicePreferredAccuracy << "% (" << totalChoicePreferredCorrect << "/" << totalChoiceNotes << ")\n";
        logFile << "  Elfogadhato lefogas: " << choiceAcceptedAccuracy << "% (" << totalChoiceAcceptedCorrect << "/" << totalChoiceNotes << ")\n";

        std::cout << "Valasztasos hangokon - kedvenc: " << choicePreferredAccuracy << "%, elfogadhato: " << choiceAcceptedAccuracy << "%\n";
    }
    logFile << "=======================================\n\n";
    std::cout << "\n";
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

int Benchmark::CountPossiblePositions(const int midiNote, const std::vector<int> &tuning)
{
    int count = 0;
    for (const int openString : tuning)
    {
        const int fretIdx = midiNote - openString;
        if (fretIdx >= 0 && fretIdx <= 24)
        {
            count++;
        }
    }
    return count;
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

        // választásos a hang, ha több helyen is lefogható
        const bool isChoice = CountPossiblePositions(testCase.inputNotes[i].GetMidiNote(), testCase.tuning) > 1;
        if (isChoice)
        {
            result.choiceTotal++;
        }

        if (matchIdx == 0)
        {
            result.preferredCorrect++;
            result.acceptedCorrect++;
            if (isChoice)
            {
                result.choicePreferredCorrect++;
                result.choiceAcceptedCorrect++;
            }
        }
        else if (matchIdx > 0)
        {
            result.acceptedCorrect++;
            if (isChoice)
            {
                result.choiceAcceptedCorrect++;
            }
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
            << "elfogadhato " << result.acceptedCorrect << "/" << result.total << " (" << acceptedAccuracy << "%)\n";

    if (result.choiceTotal > 0)
    {
        const double choicePreferredAccuracy = (static_cast<double>(result.choicePreferredCorrect) / result.choiceTotal) * 100.0;
        const double choiceAcceptedAccuracy = (static_cast<double>(result.choiceAcceptedCorrect) / result.choiceTotal) * 100.0;

        logFile << "  Valasztasos hangokon (" << result.choiceTotal << "): "
                << "kedvenc " << result.choicePreferredCorrect << "/" << result.choiceTotal << " (" << choicePreferredAccuracy << "%), "
                << "elfogadhato " << result.choiceAcceptedCorrect << "/" << result.choiceTotal << " (" << choiceAcceptedAccuracy << "%)\n\n";
    }
    else
    {
        logFile << "  Valasztasos hangokon: nincs valasztasos hang\n\n";
    }

    return result;
}
