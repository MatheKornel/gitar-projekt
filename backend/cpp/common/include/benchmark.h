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

    // ugyanezek csak a választásos hangokra (amelyek a fogólapon több helyen is lefoghatók)
    int choiceTotal = 0;
    int choicePreferredCorrect = 0;
    int choiceAcceptedCorrect = 0;
};

// a tesztek eredményeinek összesítése (teszt-alapú, hang-alapú és választásos pontosság)
class BenchmarkSummary
{
public:
    void Add(const BenchmarkResult &result);                                // egy teszt eredményének hozzáadása
    void Print(std::ofstream &logFile, const std::string &algoName) const; // végső eredmények kiírása a log fájlba és a konzolra

private:
    int validTests = 0;
    double sumPreferredAccuracy = 0.0; // tesztenkénti pontosságok összege (teszt-alapú átlaghoz)
    double sumAcceptedAccuracy = 0.0;
    int totalNotes = 0; // összes hang (hang-alapú pontossághoz)
    int totalPreferredCorrect = 0;
    int totalAcceptedCorrect = 0;
    int totalChoiceNotes = 0; // választásos hangok (több helyen is lefoghatók)
    int totalChoicePreferredCorrect = 0;
    int totalChoiceAcceptedCorrect = 0;
};

class Benchmark
{
public:
    // betölti a fájlt és visszaadja a struktúrát
    static BenchmarkCase LoadFromFile(const std::string &filepath, const std::string &testName);

    // betölti az összes benchmark tesztet a megadott mappából (új tesztet itt kell felvenni, minden eljárás ezt használja)
    static std::vector<BenchmarkCase> LoadAllCases(const std::string &benchmarkDir);

    // összehasonlítja a várt és a kapott lefogásokat, majd kiírja az eredményt
    static BenchmarkResult Evaluate(const BenchmarkCase &testCase, const std::vector<std::pair<int, int>> &actualPositions, std::ofstream &logFile);

private:
    // "3:12|4:8" formátumú szövegből húr-bund párok listája, hibás formátum esetén üres listát ad vissza
    static std::vector<std::pair<int, int>> ParsePositions(const std::string &text);

    // ellenőrzi, hogy a megadott lefogások tényleg a hanghoz tartoznak-e az adott hangolásban
    static void ValidatePositions(const BenchmarkCase &testCase);

    // húr-bund párok kiírása "3:12 | 4:8" formában
    static std::string PositionsToString(const std::vector<std::pair<int, int>> &positions);

    // hány helyen szólaltatható meg a hang az adott hangolásban (0-24. bund)
    static int CountPossiblePositions(const int midiNote, const std::vector<int> &tuning);
};
