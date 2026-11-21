from config_paths import ProjectPaths


class DataToTxtConverter:
    def __init__(self, notes, paths: ProjectPaths | None = None):
        self.notes = notes
        self.paths = paths or ProjectPaths()

    # a felismert hangok mentése Excelbe másolható formában (test_txt_to_excel mappa)
    # a C++ optimalizáló bemeneti fájlját a cpp_optimizer.py írja
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