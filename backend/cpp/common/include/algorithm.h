#pragma once

#include <string>
#include <vector>
#include "input_notes.h"
#include "note_position.h"

// Minden ujjrend optimalizáló ezt a három függvényt valósítja meg a saját mappájának algorithm.cpp fájljában.
// A közös belépési pont (common/src/app_main.cpp) ezeken keresztül hívja az algoritmust,
// így a benchmark és a fájlos futtatás kódja csak egy helyen van meg.

// az optimalizálás: hangonként egy lefogás
// verbose: fájlos futtatásnál igaz, ilyenkor az algoritmus kiírhat részeredményeket (pl. a PSO a fitneszt), a benchmarkban hamis
std::vector<NotePosition> Optimize(const std::vector<InputNotes> &notes, const bool verbose);

// az eljárás azonosítója, ebből lesz a log fájl neve: <azonosító>_benchmark_results.txt (pl. "main")
std::string AlgorithmId();

// az eljárás neve az eredményfájlokban (pl. "Sajat algoritmus")
std::string AlgorithmName();
