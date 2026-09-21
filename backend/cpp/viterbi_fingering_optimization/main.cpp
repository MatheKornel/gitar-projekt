#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include <fstream>
#include "fretboard.h"
#include "input_notes.h"
#include "viterbi.h"
#include "benchmark.h"

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        std::ofstream logFile("../../../benchmark_results/viterbi_benchmark_results.txt");
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

        double totalAccuracy = 0.0;
        int validTests = 0;

        for (const auto &test : tests)
        {
            if (test.inputNotes.empty())
                continue;

            Viterbi viterbi(test.inputNotes);
            auto optResult = viterbi.Optimization();

            std::vector<std::pair<int, int>> actualPositions;
            for (const auto &pos : optResult)
            {
                actualPositions.push_back({pos.GetStringIdx(), pos.GetFretIdx()});
            }

            double accuracy = Benchmark::Evaluate(test, actualPositions, logFile);
            totalAccuracy += accuracy;
            validTests++;
        }

        if (validTests > 0)
        {
            logFile << "Osszesitett pontossag: "
                    << (totalAccuracy / validTests) << "%\n\n";

            std::cout << "Osszesitett pontossag: "
                      << (totalAccuracy / validTests) << "%\n\n";
        }

        logFile.close();
        std::cout << "A benchmark lefutott! Keresd a 'viterbi_benchmark_results.txt' fajlt a benchmark_results mappaban.\n";

        return 0;
    }

    std::string filePath = argv[1];

    const auto input = InputNotes::LoadNotes(filePath);

    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));
    const auto result = Viterbi(input).Optimization();
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }

    return 0;
}