#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include <fstream>
#include "fretboard.h"
#include "input_notes.h"
#include "optimization.h"
#include "benchmark.h"

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        std::ofstream logFile("../../../benchmark_results/main_benchmark_results.txt");
        if (!logFile.is_open())
        {
            std::cerr << "Hiba: Nem sikerult letrehozni a log fajlt!\n";
            return 1;
        }

        logFile << "\n--- Benchmark inditasa ---\n";

        std::cout << "Benchmark futtatasa folyamatban... Az eredmenyek a fajlba irodnak.\n";

        std::vector<BenchmarkCase> tests;
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/jotun_clean_fing-opt_test.txt", "jotun_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/almost_honest_clean_fing-opt_test.txt", "almost_honest_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/ashes_in_your_mouth_clean_fing-opt_test.txt", "ashes_in_your_mouth_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/AR_Lick1_FN_fing-opt_test.txt", "AR_Lick1_FN"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/AR_Lick3_FN_fing-opt_test.txt", "AR_Lick3_FN"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/breaking_the_law_clean_fing-opt_test.txt", "breaking_the_law_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/A_0-3-5-3-0_fing-opt_test.txt", "A_0-3-5-3-0"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/A_clean_fing-opt_test.txt", "A_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/E_0-3-5-3-0_fing-opt_test.txt", "E_0-3-5-3-0"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/e0_clean_fing-opt_test.txt", "e0_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/e24_clean_fing-opt_test.txt", "e24_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/endgame_clean_fing-opt_test.txt", "endgame_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/trust_clean_fing-opt_test.txt", "trust_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/powerslave_clean_fing-opt_test.txt", "powerslave_clean"));

        int validTests = 0;
        double sumPreferredAccuracy = 0.0; // tesztenkénti pontosságok összege (teszt-alapú átlaghoz)
        double sumAcceptedAccuracy = 0.0;
        int totalNotes = 0;                // összes hang (hang-alapú pontossághoz)
        int totalPreferredCorrect = 0;
        int totalAcceptedCorrect = 0;

        for (const auto &test : tests)
        {
            if (test.inputNotes.empty())
                continue;

            FretBoard::SetTuning(test.tuning); // minden teszt a saját hangolásával fut

            Optimization opt(test.inputNotes);
            auto optResult = opt.RunOptimization();

            std::vector<std::pair<int, int>> actualPositions;
            for (const auto &pos : optResult)
            {
                actualPositions.push_back({pos.GetStringIdx(), pos.GetFretIdx()});
            }

            BenchmarkResult result = Benchmark::Evaluate(test, actualPositions, logFile);
            validTests++;
            sumPreferredAccuracy += (static_cast<double>(result.preferredCorrect) / result.total) * 100.0;
            sumAcceptedAccuracy += (static_cast<double>(result.acceptedCorrect) / result.total) * 100.0;
            totalNotes += result.total;
            totalPreferredCorrect += result.preferredCorrect;
            totalAcceptedCorrect += result.acceptedCorrect;
        }

        if (validTests > 0)
        {
            double preferredTestAccuracy = sumPreferredAccuracy / validTests;
            double acceptedTestAccuracy = sumAcceptedAccuracy / validTests;
            double preferredNoteAccuracy = (static_cast<double>(totalPreferredCorrect) / totalNotes) * 100.0;
            double acceptedNoteAccuracy = (static_cast<double>(totalAcceptedCorrect) / totalNotes) * 100.0;

            logFile << "=======================================\n";
            logFile << "VEGSO EREDMENYEK (" << validTests << " teszt, " << totalNotes << " hang):\n";
            logFile << "Kedvenc lefogas:\n";
            logFile << "  Teszt-alapu (Sulyozatlan) pontossag: " << preferredTestAccuracy << "%\n";
            logFile << "  Hang-alapu (Sulyozott) pontossag:    " << preferredNoteAccuracy << "% (" << totalPreferredCorrect << "/" << totalNotes << ")\n";
            logFile << "Elfogadhato lefogas:\n";
            logFile << "  Teszt-alapu (Sulyozatlan) pontossag: " << acceptedTestAccuracy << "%\n";
            logFile << "  Hang-alapu (Sulyozott) pontossag:    " << acceptedNoteAccuracy << "% (" << totalAcceptedCorrect << "/" << totalNotes << ")\n";
            logFile << "=======================================\n\n";

            std::cout << "Kedvenc lefogas     - teszt-alapu: " << preferredTestAccuracy << "%, hang-alapu: " << preferredNoteAccuracy << "%\n";
            std::cout << "Elfogadhato lefogas - teszt-alapu: " << acceptedTestAccuracy << "%, hang-alapu: " << acceptedNoteAccuracy << "%\n\n";
        }

        logFile.close();
        std::cout << "A benchmark lefutott! Keresd a 'main_benchmark_results.txt' fajlt a benchmark_results mappaban.\n";

        return 0;
    }

    std::string filePath = argv[1];

    const auto input = InputNotes::LoadNotes(filePath);

    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));
    const auto result = Optimization(input).RunOptimization();
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }

    return 0;
}