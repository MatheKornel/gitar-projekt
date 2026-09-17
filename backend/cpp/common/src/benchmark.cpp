#include "benchmark.h"
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>

BenchmarkCase Benchmark::LoadFromFile(const std::string &filepath, const std::string &testName)
{
    BenchmarkCase bc;
    bc.testName = testName;
    std::ifstream file(filepath);

    if (!file.is_open())
    {
        std::cerr << "[!] Hiba a benchmark fajl megnyitasakor: " << filepath << "\n";
        return bc;
    }

    std::string line;
    while (std::getline(file, line))
    {
        if (line.empty() || line[0] == '#')
            continue;

        std::istringstream iss(line);
        int midi, stringIdx, fretIdx;
        double onset, duration;
        std::string name;

        if (iss >> midi >> onset >> duration >> name >> stringIdx >> fretIdx)
        {
            bc.inputNotes.push_back(InputNotes(midi, onset, duration, name));
            bc.expectedPositions.push_back({stringIdx, fretIdx});
        }
    }
    return bc;
}

double Benchmark::Evaluate(const BenchmarkCase &testCase, const std::vector<std::pair<int, int>> &actualPositions)
{
    std::cout << "Futtatas: [" << testCase.testName << "]\n";

    int total = testCase.expectedPositions.size();

    if (actualPositions.size() != total)
    {
        std::cout << "  [!] HIBA: Kimenet merete nem egyezik! Vart: " << total << ", Kapott: " << actualPositions.size() << "\n\n";
        return 0.0;
    }

    int correct = 0;
    for (size_t i = 0; i < total; i++)
    {
        // várt húr és bund
        int expString = testCase.expectedPositions[i].first;
        int expFret = testCase.expectedPositions[i].second;

        // kapott (optimalizált) húr és bund
        int actString = actualPositions[i].first;
        int actFret = actualPositions[i].second;

        if (expString == actString && expFret == actFret)
        {
            correct++;
        }
        else
        {
            std::cout << "  - Hiba a(z) " << (i + 1) << ". hangnal (" << testCase.inputNotes[i].GetNoteName() << "): "
                      << "Vart -> Hur:" << expString << " Bund:" << expFret
                      << " | Kapott -> Hur:" << actString << " Bund:" << actFret << "\n";
        }
    }

    double accuracy = (static_cast<double>(correct) / total) * 100.0;
    std::cout << "  Eredmeny: " << correct << "/" << total << " helyes ("
              << std::fixed << std::setprecision(1) << accuracy << "%)\n\n";

    return accuracy;
}