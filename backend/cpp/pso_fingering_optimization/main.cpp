#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include <fstream>
#include "fretboard.h"
#include "input_notes.h"
#include "particle.h"
#include "pso.h"
#include "benchmark.h"

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        std::ofstream logFile("../../../benchmark_results/pso_benchmark_results.txt");
        if (!logFile.is_open())
        {
            std::cerr << "Hiba: Nem sikerult letrehozni a log fajlt!\n";
            return 1;
        }

        logFile << "\n--- Benchmark inditasa ---\n";
        std::cout << "PSO Benchmark futtatasa folyamatban... Az eredmenyek a fajlba irodnak.\n";

        std::vector<BenchmarkCase> tests = Benchmark::LoadAllCases("../../../benchmarks");
        BenchmarkSummary summary;

        for (const auto &test : tests)
        {
            if (test.inputNotes.empty())
                continue;

            FretBoard::SetTuning(test.tuning); // minden teszt a saját hangolásával fut

            // PSO inicializálása a benchmark teszt adataival
            PSO pso(test.inputNotes, test.inputNotes.size(), 50, 10000, 0.0001);
            auto optResult = pso.PsoAlgo(5000, 0);

            std::vector<std::pair<int, int>> actualPositions;
            for (const auto &pos : optResult)
            {
                actualPositions.push_back({pos.GetStringIdx(), pos.GetFretIdx()});
            }

            BenchmarkResult result = Benchmark::Evaluate(test, actualPositions, logFile);
            summary.Add(result);
        }

        summary.Print(logFile, "PSO algoritmus");

        logFile.close();
        std::cout << "A benchmark lefutott! Keresd a 'pso_benchmark_results.txt' fajlt a benchmark_results mappaban.\n";

        return 0;
    }

    std::string filePath = argv[1];
    const auto input = InputNotes::LoadNotes(filePath);

    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));

    if (input.empty())
    {
        std::cerr << "Hiba: Nem sikerult hangokat betolteni a(z) " << filePath << " fajlbol!" << std::endl;
        return 1;
    }

    PSO pso(input, input.size(), 50, 10000, 0.0001);
    const auto result = pso.PsoAlgo(5000, 100);
    std::cout << "Fitnesz: " << pso.g_opt_fitness << std::endl;
    std::cout << "Optimalis lefogasok:" << std::endl;
    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }

    return 0;
}