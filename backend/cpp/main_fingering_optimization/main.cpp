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

        std::vector<BenchmarkCase> tests = Benchmark::LoadAllCases("../../../benchmarks");
        BenchmarkSummary summary;

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
            summary.Add(result);
        }

        summary.Print(logFile, "Sajat algoritmus");
        summary.SaveToSummaryFile("../../../benchmark_results/osszesitett_eredmenyek.txt", "Sajat algoritmus");

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