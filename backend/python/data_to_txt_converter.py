from config_paths import ProjectPaths


class DataToTxtConverter:
    def __init__(self, notes, paths: ProjectPaths | None = None):
        self.notes = notes
        self.paths = paths or ProjectPaths()

    def save_note_to_txt(self, algo, file_name="notes.txt"):
        notes = self.notes
        output_path = self.paths.cpp_project_dir(algo) / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output_path.open("w", encoding="utf-8") as f:
                f.write(f"{len(notes)}\n")
                for note in notes:
                    note_name = note.note_name.replace("♯", "#")
                    f.write(f"{int(note.midi_note)} {note.onset:.4f} {note.duration:.4f} {note_name}\n")
            print(f"Hangok sikeresen elmentve: {output_path}")
        except Exception as e:
            print(f"Sikertelen mentés: {e}")

    def save_to_test_txt(self, output_txt_path="sajat_program_adatok.txt"):
        notes_list = self.notes
        output_path = self.paths.output_path(output_txt_path, kind="test")
        with output_path.open("w", encoding="utf-8") as f:
            f.write("MIDI\tHang\tOnset\tOffset\n")

            for note in notes_list:
                onset = f"{note.onset:.3f}".replace(".", ",")
                offset = f"{note.offset:.3f}".replace(".", ",")
                note_name = note.note_name.replace("♯", "#")
                f.write(f"{note.midi_note}\t{note_name}\t{onset}\t{offset}\n")

        print(f"Teszt adatok mentve: {output_path}")