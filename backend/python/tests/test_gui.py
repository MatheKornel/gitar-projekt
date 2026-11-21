# A GUI (main.py) néhány viselkedésének tesztje ablak megjelenítése nélkül.
import sys
import tkinter as tk
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import GuitarProjectApp
from note_event import NoteEvent


# egyetlen közös alkalmazás a modul összes tesztjéhez: Windowson ha egy folyamat sokszor hoz létre Tk ablakot,
# az időnként "Can't find a usable tk.tcl" hibával elszáll; ezért minden teszt maga állítja be a szükséges állapotot
@pytest.fixture(scope="module")
def app():
    try:
        application = GuitarProjectApp()
    except tk.TclError as e:
        pytest.skip(f"nincs elérhető grafikus felület (Tk): {e}")
    application.root.withdraw()  # az ablak ne jelenjen meg
    yield application
    application.root.destroy()


def test_refresh_ui_does_not_create_new_widgets(app):
    widget_count = len(app.root.winfo_children())
    for _ in range(5):
        app.is_note_rec_done = not app.is_note_rec_done
        app.refresh_ui()
    assert len(app.root.winfo_children()) == widget_count


def test_refresh_ui_updates_status_texts(app):
    app.original_audio = None
    app.is_note_rec_done = True
    app.refresh_ui()
    assert app.note_rec_status_label.cget("text") == "Hangfelismerés: kész"
    assert app.loaded_file_label.cget("text") == "Betöltött fájl: nincs"


@pytest.mark.parametrize("text, expected", [("120", 120), (" 95 ", 95), ("abc", None), ("", None), ("12.5", None), ("0", None), ("-40", None)])
def test_read_bpm(app, text, expected):
    app.bpm_entry.delete(0, tk.END)
    app.bpm_entry.insert(0, text)
    assert app._read_bpm() == expected


def test_save_midi_with_invalid_bpm_does_not_crash(app, tmp_path):
    app.current_notes = [NoteEvent(0.0, 0.5, 440.0)]
    app.original_filepath = str(tmp_path / "proba_gui_teszt.wav")
    app.bpm_entry.delete(0, tk.END)
    app.bpm_entry.insert(0, "abc")
    app.save_midi()  # korábban itt ValueError kivétel keletkezett
    assert not app.paths.output_path("proba_gui_teszt.mid", kind="midi").exists()
