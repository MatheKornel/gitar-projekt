#pragma once

#include <string>
#include <vector>
#include <utility>
#include <fstream>
#include "input_notes.h"

// egyetlen teszteset adatai
struct BenchmarkCase
{
    std::string testName;
    std::vector<InputNotes> inputNotes;
    std::vector<std::pair<int, int>> expectedPositions; // húr-bund párok listája
};

class Benchmark
{
public:
    // betölti a fájlt és visszaadja a struktúrát
    static BenchmarkCase LoadFromFile(const std::string &filepath, const std::string &testName);

    // összehasonlítja a várt és a kapott számokat, majd kiírja az eredményt
    static double Evaluate(const BenchmarkCase &testCase, const std::vector<std::pair<int, int>> &actualPositions, std::ofstream &logFile);
};