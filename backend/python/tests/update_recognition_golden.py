# A hangfelismerés golden fájljának (tests/data/recognition_golden.json) újragenerálása.
# Csak akkor kell futtatni, ha a hangfelismerés SZÁNDÉKOSAN változott, és a benchmark alapján az új eredmény jobb.
# Használat: python backend/python/tests/update_recognition_golden.py
import contextlib
import io

from recognition_regression import GOLDEN_PATH, audio_path, case_names, load_golden, run_case, save_golden


def main():
    golden = {}
    if GOLDEN_PATH.is_file():
        golden = load_golden()

    print(f"{'Teszt':<50} | {'TP':>3} | {'FP':>3} | {'FN':>3} | {'Hangok':>6}")
    for name in case_names():
        if audio_path(name) is None:
            print(f"{name:<50} | kimarad (nincs hangfájl), a régi golden érték megmarad")
            continue
        with contextlib.redirect_stdout(io.StringIO()):  # a hangfelismerés részletes kiírása itt csak zaj
            result = run_case(name)
        golden[name] = result
        print(f"{name:<50} | {result['tp']:>3} | {result['fp']:>3} | {result['fn']:>3} | {len(result['notes']):>6}")

    save_golden(golden)
    print(f"\nGolden fájl mentve: {GOLDEN_PATH}")


if __name__ == "__main__":
    main()
