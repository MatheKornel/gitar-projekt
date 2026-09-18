import argparse
import subprocess
import os
from config_paths import ProjectPaths

def main():
    parser = argparse.ArgumentParser(description="Gitár ujjrend optimalizáló benchmark futtatása.")
    parser.add_argument("-a", "--algo", required=True, 
                        choices=['main', 'viterbi', 'pso', 'main_plus_viterbi'],
                        help="Az optimalizáló eljárás neve.")
    args = parser.parse_args()

    paths = ProjectPaths()
    cpp_exe = paths.cpp_executable(args.algo)

    if not cpp_exe.exists():
        print(f"[!] Hiba: Nem talalhato a futtathato fajl: {cpp_exe}")
        print("Ellenorizd, hogy leforditottad-e a C++ kodot ehhez az algoritmushoz!")
        return

    print(f"[{args.algo.upper()}] Benchmark inditasa a hatterben...")
    
    # paraméter nélküli futtatás, ami a C++ kódban a benchmarkot indítja el
    result = subprocess.run([str(cpp_exe)], cwd=str(cpp_exe.parent), capture_output=True, text=True)
    
    # ha a C++ program írt a standard outputra vagy errorra, azt kiírjuk
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print("[!] C++ Hiba / Figyelmeztetes:")
        print(result.stderr.strip())
    
    # megkeressük és beolvassuk a legenerált log fájlt
    log_path = os.path.join(str(cpp_exe.parent), f"../../../benchmarks/{args.algo}_benchmark_results.txt")
    log_path = os.path.normpath(log_path)
    
    if os.path.exists(log_path):
        print("\n" + "="*50)
        print(f" EREDMENYEK ({args.algo})")
        print("="*50)
        with open(log_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"[!] Figyelem: A {args.algo}_benchmark_results.txt nem jott letre.")

if __name__ == "__main__":
    main()