## Program célja
A program célja, hogy egy gitárjátékot tartalmazó audio fájlból értelmes, használható kottát és tabulatúrát tudjon generálni. Legfőbb feladatai a jel szűrése, az alaphangok felismerése és azok optimalizálása a helyes ujjrend szerint.

## Főbb funkciók
- __zajszűrés__ sáváteresztő szűrővel
- __hangfelismerés__ STFT és HS módszerek kombinálásával
- __időzítés__ S-transzformációval és _salience_ érték követéssel
- __MIDI formátumba konvertálás__
- __ujjrend optimalizálás__

## Használt technológiák
- Python
- NumPy
- Librosa
- Scipy
- SoundFile
- Tkinter

## Mappastruktúra
```
gitar-projekt/
├── audio_files/     # Tesztelhető audo fájlok
├── backend/         # Program fő fájlai
│ └── audio_files.py
| └── filter.py
| └── main.py
| └── note_recognition.py
| └── spectrograms.py
├── .gitignore
├── README.md
```
