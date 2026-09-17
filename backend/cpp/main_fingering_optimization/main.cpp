#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include "fretboard.h"
#include "input_notes.h"
#include "optimization.h"
#include "benchmark.h"

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        std::cout << "\n--- Benchmark inditasa ---\n";

        std::vector<BenchmarkCase> tests;
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/jotun_clean_fing-opt_test.txt", "jotun_clean"));
        tests.push_back(Benchmark::LoadFromFile("../../../benchmarks/almost_honest_clean_fing-opt_test.txt", "almost_honest_clean"));

        double totalAccuracy = 0.0;
        int validTests = 0;

        for (const auto &test : tests)
        {
            if (test.inputNotes.empty())
                continue;

            Optimization opt(test.inputNotes);
            auto optResult = opt.RunOptimization();

            std::vector<std::pair<int, int>> actualPositions;
            for (const auto &pos : optResult)
            {
                actualPositions.push_back({pos.GetStringIdx(), pos.GetFretIdx()});
            }

            double accuracy = Benchmark::Evaluate(test, actualPositions);
            totalAccuracy += accuracy;
            validTests++;
        }

        if (validTests > 0)
        {
            std::cout << "Osszesitett pontossag: "
                      << (totalAccuracy / validTests) << "%\n\n";
        }

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