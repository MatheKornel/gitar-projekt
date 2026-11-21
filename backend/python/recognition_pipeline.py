import soundfile as sf

from filter import BandpassFilter
from guitar_note_freqs import GuitarNoteFreqs
from note_recognition import ShortTimeFT
from onset_histogram import estimate_bpm

MAX_HARMONICS = 5           # ennyi felharmonikust nézünk a hangmagasság becslésénél
LOWCUT_FACTOR = 0.85        # a sáváteresztő alsó határa a hangolás legmélyebb hangjához képest
HIGHCUT_FACTOR = 2.12       # a sáváteresztő felső határa a legmagasabb hanghoz képest


# hangfájl betöltése, sztereó esetén a két csatorna átlaga
def load_audio(path):
    audio, fs = sf.read(path)
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    return audio, fs


# a sáváteresztő szűrő határai a hangolás alapján
def filter_cutoffs(tuning):
    guitar_notes = GuitarNoteFreqs().select_tuning(tuning)
    return guitar_notes[0] * LOWCUT_FACTOR, guitar_notes[-1] * HIGHCUT_FACTOR


# a teljes hangfelismerés: szűrés, hangfelismerés és tempóbecslés
# ezt használja a GUI és a regressziós teszt is, így a kettő biztosan ugyanazt futtatja
# visszaad: szűrt jel, felismert hangok (NoteEvent lista), becsült BPM
def recognize(audio, fs, tuning="E"):
    lowcut, highcut = filter_cutoffs(tuning)
    bpf = BandpassFilter(audio)
    filtered = bpf.bandpass_filter(audio, fs, lowcut=lowcut, highcut=highcut)
    print("Szűrés elvégezve.")

    stft = ShortTimeFT(filtered, fs=fs)
    print("Elemzés folyamatban...")
    notes = stft.note_rec(MAX_HARMONICS, tuning)

    # tempóbecslés az onsetek közti időkből (IOI hisztogram)
    bpm = estimate_bpm(stft.onsets)
    return filtered, notes, bpm
