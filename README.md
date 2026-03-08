# Gitár kotta és tabulatúra generálása az ujjrend optimalizálásával (folyamatban)

## Program célja
A program célja, hogy egy gitárjátékot tartalmazó audio fájlból értelmes, használható kottát és tabulatúrát tudjon generálni. Legfőbb feladatai a jel szűrése, az alaphangok pontos felismerése, valamint ezek optimalizálása a helyes gitáros ujjrend szerint. 

## Főbb funkciók
- **Zajszűrés:** Sáváteresztő (bandpass) szűrő alkalmazása az alapvető frekvenciatartományon kívüli zajok eltávolítására.
- **Időzítés (Onset és Offset detektálás):** Spectral Flux módszer alkalmazása STFT alapon. A felismerést Gauss-simítás teszi robusztussá, kiküszöbölve a pengetési mikrozajokból adódó duplikációkat (fals pozitív találatokat). Az offseteket adaptív salience-követés határozza meg.
- **Hangfelismerés:** STFT és Harmonic Summation (HS) módszerek kombinálása a legstabilabb alaphang (F0) kiválasztására.
- **Tempó becslés:** Inter-Onset Interval (IOI) hisztogram alapú BPM kalkuláció.
- **Kotta és MIDI export:** A felismert hangokból automatikus MIDI fájl, valamint LilyPond és music21 segítségével formázott PDF kotta generálása.
- **Ujjrend optimalizálás:** Viterbi algoritmus alapú ujjrend optimalizálás. (Megjegyzés: A korábbi PSO algoritmus megközelítés elvetésre került, a Viterbi alapú optimalizálás jelenleg korai fejlesztési fázisban van).
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

## Mappastruktúra
```text
gitar-projekt/
├── audio_files/                             # Tesztelhető audio fájlok
├── backend/                                 # Program fő fájlai
│    ├── python/
│    │   ├── audio_files.py                  # Audio adatok kezelése
│    │   ├── filter.py                       # Sáváteresztő szűrő
│    │   ├── main.py                         # GUI és a program belépési pontja
│    │   ├── midi.py                         # MIDI fájl exportálása
│    │   ├── note_event.py                   # Felismert hangok adatmodellje
│    │   ├── note_recognition.py             # STFT és HS alapú hangfelismerés, offset detektálás
│    │   ├── onset_detect.py                 # Spectral Flux alapú onset detektálás
│    │   ├── onset_histogram.py              # IOI hisztogram és BPM becslés
│    │   ├── sheet_music_exporter.py         # Kotta generálása (music21/LilyPond)
│    │   └── spectrograms.py                 # Spektrogramok vizualizációja
│    ├── cpp/
│    │   ├── pso_fingering_optimization/     # C++ alapú PSO ujjrend optimalizáló (elvetve)
│    │   └── viterbi_fingering_optimization/ # C++ alapú Viterbi ujjrend optimalizáló (fejlesztés alatt)
├── MIDI_files/                              # Eddigi tesztek során a legutóbbi generált MIDI fájlok
├── sheet_music/                             # Eddigi tesztek során a legutóbbi generált kották
├── .gitignore
└── README.md