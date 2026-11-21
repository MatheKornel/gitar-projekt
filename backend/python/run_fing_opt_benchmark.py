import argparse
import os
from config_paths import ProjectPaths
from cpp_optimizer import ALGORITHMS, CppOptimizer


def run_benchmark(paths, algo, print_log):
    optimizer = CppOptimizer(algo, paths)

    if not optimizer.exists():
        print(f"[!] Hiba: Nem talalhato a futtathato fajl: {optimizer.cpp_exe}")
        print("Ellenorizd, hogy leforditottad-e a C++ kodot ehhez az algoritmushoz!")
        return

    print(f"[{algo.upper()}] Benchmark inditasa a hatterben...")

    result = optimizer.run_benchmark()

    # ha a C++ program írt a standard outputra vagy errorra, azt kiírjuk
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print("[!] C++ Hiba / Figyelmeztetes:")
        print(result.stderr.strip())

    if not print_log:
        return

    # megkeressük és beolvassuk a legenerált log fájlt
    log_path = optimizer.benchmark_log_path()

    if os.path.exists(log_path):
        print("\n" + "="*50)
        print(f" EREDMENYEK ({algo})")
        print("="*50)
        with open(log_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"[!] Figyelem: A {algo}_benchmark_results.txt nem jott letre.")


def main():
    parser = argparse.ArgumentParser(description="Gitár ujjrend optimalizáló benchmark futtatása.")
    parser.add_argument("-a", "--algo", required=True,
                        choices=ALGORITHMS + ['all'],
                        help="Az optimalizáló eljárás neve ('all' esetén mind a négy lefut).")
    args = parser.parse_args()

    paths = ProjectPaths()

    if args.algo != 'all':
        run_benchmark(paths, args.algo, True)
        return

    # mind a négy eljárás lefut, a végén csak az összesítő táblázatot írjuk ki
    for algo in ALGORITHMS:
        run_benchmark(paths, algo, False)

    summary_path = CppOptimizer('main', paths).benchmark_summary_path()
    if os.path.exists(summary_path):
        print("\n" + "="*50)
        print(" OSSZESITETT EREDMENYEK")
        print("="*50)
        with open(summary_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("[!] Figyelem: Az osszesitett_eredmenyek.txt nem jott letre.")

if __name__ == "__main__":
    main()