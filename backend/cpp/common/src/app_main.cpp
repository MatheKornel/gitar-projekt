#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include <fstream>
#include <chrono>
#include "algorithm.h"
#include "fretboard.h"
#include "input_notes.h"
#include "benchmark.h"

// A négy ujjrend optimalizáló közös belépési pontja. Az algoritmust az algorithm.h függvényein keresztül hívja,
// ezeket mindegyik eljárás a saját mappájának algorithm.cpp fájljában valósítja meg.
//   - paraméter nélkül: benchmark a benchmarks mappa tesztjein, az eredmény a benchmark_results mappába kerül
//   - egy paraméterrel (notes.txt útvonala): a fájlban lévő hangok optimalizálása, a lefogások a standard kimenetre kerülnek

// az útvonalak a program mappájához (backend/cpp/<eljárás>) képest értendők, a Python ebből a mappából indítja
const std::string benchmarkDir = "../../../benchmarks";
const std::string resultsDir = "../../../benchmark_results";

int RunBenchmark()
{
    const std::string logFileName = AlgorithmId() + "_benchmark_results.txt";
    std::ofstream logFile(resultsDir + "/" + logFileName);
    if (!logFile.is_open())
    {
        std::cerr << "Hiba: Nem sikerult letrehozni a log fajlt!\n";
        return 1;
    }

    logFile << "\n--- Benchmark inditasa ---\n";

    std::cout << "Benchmark futtatasa folyamatban... Az eredmenyek a fajlba irodnak.\n";

    std::vector<BenchmarkCase> tests = Benchmark::LoadAllCases(benchmarkDir);
    BenchmarkSummary summary;

    for (const auto &test : tests)
    {
        if (test.inputNotes.empty())
            continue;

        FretBoard::SetTuning(test.tuning); // minden teszt a saját hangolásával fut

        const auto optResult = Optimize(test.inputNotes, false);

        std::vector<std::pair<int, int>> actualPositions;
        for (const auto &pos : optResult)
        {
            actualPositions.push_back({pos.GetStringIdx(), pos.GetFretIdx()});
        }

        BenchmarkResult result = Benchmark::Evaluate(test, actualPositions, logFile);
        summary.Add(result);
    }

    summary.Print(logFile, AlgorithmName());
    summary.SaveToSummaryFile(resultsDir + "/osszesitett_eredmenyek.txt", AlgorithmName());

    logFile.close();
    std::cout << "A benchmark lefutott! Keresd a '" << logFileName << "' fajlt a benchmark_results mappaban.\n";

    return 0;
}

int RunFile(const std::string &filePath)
{
    const auto input = InputNotes::LoadNotes(filePath);

    FretBoard::SetTuning(InputNotes::LoadTuning(filePath));

    if (input.empty())
    {
        std::cerr << "Hiba: Nem sikerult hangokat betolteni a(z) " << filePath << " fajlbol!" << std::endl;
        return 1;
    }

    // csak magát az optimalizálást mérjük (a program indítása és a fájlbeolvasás nélkül)
    const auto startTime = std::chrono::steady_clock::now();
    const auto result = Optimize(input, true);
    const auto endTime = std::chrono::steady_clock::now();
    const double elapsedMs = std::chrono::duration<double, std::milli>(endTime - startTime).count();
    std::cerr << "Optimalizalas ideje: " << elapsedMs << " ms" << std::endl; // stderr-re, hogy a lefogások feldolgozását ne zavarja

    for (size_t i = 0; i < result.size(); i++)
    {
        std::cout << input[i].GetNoteName() << "\t-\t" << result[i].ToString() << std::endl;
    }

    return 0;
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        return RunBenchmark();
    }
    return RunFile(argv[1]);
}
