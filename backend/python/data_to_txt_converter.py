import os

class DataToTxtConverter:
    def __init__(self, notes):
        self.notes = notes

    def save_note_to_txt(self, algo, file_name="notes.txt"):
        notes = self.notes
        path = f"D:\\Sulis dolgok\\gitar_projekt\\backend\\cpp\\{algo}_fingering_optimization\\"
        try:
            with open(os.path.join(path, file_name), "w") as f:
                f.write(f"{len(notes)}\n")
                for note in notes:
                    note_name = note.note_name.replace('\u266f', '#')
                    f.write(f"{int(note.midi_note)} {note.onset:.4f} {note.duration:.4f} {note_name}\n")
            print(f"Hangok sikeresen elmentve: {file_name}")
        except Exception as e:
            print(f"Sikertelen mentés: {e}")


    def save_to_test_txt(self, output_txt_path="sajat_program_adatok.txt"):
        notes_list = self.notes
        path = "D:\\Sulis dolgok\\gitar_projekt\\test_txt_to_excel\\"
        with open(os.path.join(path, output_txt_path), 'w', encoding='utf-8') as f:
            f.write("MIDI\tHang\tOnset\tOffset\n")
            
            for note in notes_list:
                onset = f"{note.onset:.3f}".replace('.', ',')
                offset = f"{note.offset:.3f}".replace('.', ',')
                note_name = note.note_name.replace('\u266f', '#')
                f.write(f"{note.midi_note}\t{note_name}\t{onset}\t{offset}\n")
            
        print(f"Teszt adatok mentve: {output_txt_path}")