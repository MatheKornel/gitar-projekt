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
    std::vector<int> tuning; // a 6 üres húr MIDI hangmagassága (a fájl "# tuning:" sorából, alapértelmezetten standard E)
    std::vector<InputNotes> inputNotes;
    std::vector<std::vector<std::pair<int, int>>> acceptedPositions; // hangonként az elfogadható húr-bund párok, az első a kedvenc lefogás
};

// egy teszteset kiértékelésének eredménye
struct BenchmarkResult
{
    int total = 0;            // hangok száma
    int preferredCorrect = 0; // ahol a kedvenc (első) lefogást adta az algoritmus
    int acceptedCorrect = 0;  // ahol bármelyik elfogadható lefogást adta az algoritmus
};

class Benchmark
{
public:
    // betölti a fájlt és visszaadja a struktúrát
    static BenchmarkCase LoadFromFile(const std::string &filepath, const std::string &testName);

    // összehasonlítja a várt és a kapott lefogásokat, majd kiírja az eredményt
    static BenchmarkResult Evaluate(const BenchmarkCase &testCase, const std::vector<std::pair<int, int>> &actualPositions, std::ofstream &logFile);

private:
    // "3:12|4:8" formátumú szövegből húr-bund párok listája, hibás formátum esetén üres listát ad vissza
    static std::vector<std::pair<int, int>> ParsePositions(const std::string &text);

    // ellenőrzi, hogy a megadott lefogások tényleg a hanghoz tartoznak-e az adott hangolásban
    static void ValidatePositions(const BenchmarkCase &testCase);

    // húr-bund párok kiírása "3:12 | 4:8" formában
    static std::string PositionsToString(const std::vector<std::pair<int, int>> &positions);
};
