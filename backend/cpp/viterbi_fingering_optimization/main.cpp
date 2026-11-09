#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include <fstream>
#include <chrono>
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

        std::vector<BenchmarkCase> tests = Benchmark::LoadAllCases("../../../benchmarks");
        BenchmarkSummary summary;

        for (const auto &test : tests)
        {
            if (test.inputNotes.empty())
                continue;

            FretBoard::SetTuning(test.tuning); // minden teszt a saját hangolásával fut

            Viterbi viterbi(test.inputNotes);
            auto optResult = viterbi.Optimization();

            std::vector<std::pair<int, int>> actualPositions;
            for (const auto &pos : optResult)
            {
                actualPositions.push_back({pos.GetStringIdx(), pos.GetFretIdx()});
            }

            BenchmarkResult result = Benchmark::Evaluate(test, actualPositions, logFile);
            summary.Add(result);
        }

        summary.Print(logFile, "Viterbi algoritmus");
        summary.SaveToSummaryFile("../../../benchmark_results/osszesitett_eredmenyek.txt", "Viterbi algoritmus");

        logFile.close();
        std::cout << "A benchmark lefutott! Keresd a 'viterbi_benchmark_results.txt' fajlt a benchmark_results mappaban.\n";

        return 0;
    }

    std::string filePath = argv[1];

    const auto input = InputNotes::LoadNotes(filePath);

    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));

    // csak magát az optimalizálást mérjük (a program indítása és a fájlbeolvasás nélkül)
    const auto startTime = std::chrono::steady_clock::now();
    const auto result = Viterbi(input).Optimization();
    const auto endTime = std::chrono::steady_clock::now();
    const double elapsedMs = std::chrono::duration<double, std::milli>(endTime - startTime).count();
    std::cerr << "Optimalizalas ideje: " << elapsedMs << " ms" << std::endl; // stderr-re, hogy a lefogások feldolgozását ne zavarja

    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }

    return 0;
}