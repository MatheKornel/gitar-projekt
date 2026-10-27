# Gitár kotta és tabulatúra generálása az ujjrend optimalizálásával

## Program célja
A program célja, hogy egy gitárjátékot tartalmazó audio fájlból értelmes, használható kottát és tabulatúrát tudjon generálni. Legfőbb feladatai a jel szűrése, az alaphangok pontos felismerése, valamint ezek optimalizálása a helyes gitáros ujjrend szerint. 

## Főbb funkciók
- **Zajszűrés:** Sáváteresztő (bandpass) szűrő alkalmazása az alapvető frekvenciatartományon kívüli zajok eltávolítására.
- **Időzítés (Onset és Offset detektálás):** Spectral Flux módszer alkalmazása STFT alapon. A felismerést Gauss-simítás teszi robusztussá, kiküszöbölve a pengetési mikrozajokból adódó duplikációkat (fals pozitív találatokat). Az offseteket adaptív salience-követés határozza meg.
- **Hangfelismerés:** STFT és Harmonic Summation (HS) módszerek kombinálása a legstabilabb alaphang (F0) kiválasztására.
- **Hangolás választás:** Standard E hangolástól F-ig lefelé hangolt gitárok támogatása, a hangfelismerés, a szűrő és a tabulatúra a választott hangoláshoz igazodik.
- **Tempó becslés:** Inter-Onset Interval (IOI) hisztogram alapú BPM kalkuláció.
- **Kotta és MIDI export:** A felismert hangokból automatikus MIDI fájl, valamint LilyPond és music21 segítségével formázott PDF kotta generálása.
- **Ujjrend optimalizálás:** Saját, kézpozíciós költségmodellen és dinamikus programozáson alapuló ujjrend optimalizálás (C++). Összehasonlításként a Viterbi, a PSO és a Saját + Viterbi algoritmus is választható.
- **Ujjrend benchmark:** Kézzel ellenőrzött lefogásokat tartalmazó tesztek, amelyeken mind a négy optimalizáló pontossága mérhető és összesíthető.
- **Grafikus felület:** Egyelőre kezdetleges Tkinter alapú GUI a fájlok betöltéséhez, a spektrogramok összehasonlításához és a funkciók futtatásához.

## Használt technológiák
- Python
- NumPy
- Librosa
- SciPy
- SoundFile
- Tkinter
- Mido (MIDI generáláshoz)
- music21 és LilyPond (Kotta generáláshoz)
- C++ és CMake (Ujjrend optimalizáláshoz)

## Telepítés és futtatás
1. Python csomagok telepítése (Python 3.11 vagy újabb):
   ```bash
   pip install -r requirements.txt
   ```
2. LilyPond 2.24 telepítése. Az elérési utat a program a `LILYPOND_PATH` környezeti változóból, a projekt gyökerében lévő `lilypond_path.txt` fájlból vagy a PATH-ról olvassa be.
3. A C++ ujjrend optimalizálók fordítása (a `main.exe` fájlok az algoritmusok mappáiba kerülnek):
   ```bash
   cmake -S backend/cpp -B backend/cpp/build
   cmake --build backend/cpp/build --config Release
   ```
4. A program indítása:
   ```bash
   python backend/python/main.py
   ```
5. Ujjrend benchmark parancssorból (`main`, `viterbi`, `pso`, `main_plus_viterbi` vagy `all`):
   ```bash
   python backend/python/run_fing_opt_benchmark.py -a all
   ```

## Mappastruktúra
```text
gitar-projekt/
├── audio_files/                                      # Tesztelhető audio fájlok
├── backend/                                          # Program fő fájlai
│    ├── python/
│    │   ├── audio_files.py                           # Audio adatok kezelése
│    │   ├── config_parameters.py                     # Beállítások (STFT, kvantálás, LilyPond elérési út)
│    │   ├── config_paths.py                          # Projekt mappák és fájlok elérési útjai
│    │   ├── data_to_txt_converter.py                 # Felismert hangok mentése a C++ optimalizálónak
│    │   ├── filter.py                                # Sáváteresztő szűrő
│    │   ├── guitar_note_freqs.py                     # Gitár hangok frekvenciái és hangolások
│    │   ├── main.py                                  # GUI és a program belépési pontja
│    │   ├── midi.py                                  # MIDI fájl exportálása
│    │   ├── note_event.py                            # Felismert hangok adatmodellje
│    │   ├── note_recognition.py                      # STFT és HS alapú hangfelismerés, offset detektálás
│    │   ├── onset_detect.py                          # Spectral Flux alapú onset detektálás
│    │   ├── onset_histogram.py                       # IOI hisztogram és BPM becslés
│    │   ├── quantizing.py                            # Hangok kvantálása a kottához
│    │   ├── run_fing_opt_benchmark.py                # Ujjrend benchmark futtatása parancssorból
│    │   ├── sheet_music_tab_exporter.py              # Kotta és tabulatúra generálása (music21/LilyPond)
│    │   ├── spectrograms.py                          # Spektrogramok vizualizációja
│    │   └── tests/                                   # Tesztek (pytest)
│    ├── cpp/
│    │   ├── common/                                  # Közös kód (fogólap, bemenet, benchmark)
│    │   ├── main_fingering_optimization/             # C++ alapú saját ujjrend optimalizáló
│    │   ├── main_plus_viterbi_fingering_optimization/ # C++ alapú Saját + Viterbi ujjrend optimalizáló (összehasonlításhoz)
│    │   ├── pso_fingering_optimization/              # C++ alapú PSO ujjrend optimalizáló (összehasonlításhoz)
│    │   ├── viterbi_fingering_optimization/          # C++ alapú Viterbi ujjrend optimalizáló (összehasonlításhoz)
│    │   └── CMakeLists.txt                           # A C++ optimalizálók fordítása
├── benchmarks/                                       # Ujjrend benchmark tesztek (elvárt lefogások)
├── benchmark_results/                                # Benchmark eredmények és összesítés
├── MIDI_files/                                       # Eddigi tesztek során a legutóbbi generált MIDI fájlok
├── sheet_music/                                      # Eddigi tesztek során a legutóbbi generált kották
├── .gitignore
├── requirements.txt
└── README.md
```
