import mido
import numpy as np

class MidiExporter:
    def __init__(self, ppqn=480, tempo=120):
        self.ppqn = ppqn
        self.tempo = tempo
        self.ticks_per_sec = self.ppqn * (self.tempo / 60) # 1 mp alatt hány tick van
    
    def create_midi(self, notes, output="output.mid"):
        mid = mido.MidiFile(ticks_per_beat=self.ppqn)
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # tempó beállítása
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(self.tempo)))

        # esemény lista -- minden hanghoz tartozik note_on és note_off esemény
        events = []
        for note in notes:
            events.append({'time_sec': note.onset, 'type': 'note_on', 'note': note.midi_note, 'velocity': note.velocity})
            events.append({'time_sec': note.offset, 'type': 'note_off', 'note': note.midi_note, 'velocity': note.velocity})
        
        events.sort(key=lambda x: x['time_sec']) # időrendbe rendezés

        # események hozzáadása a MIDI trackhez delta idővel
        last_event_time_sec = 0.0
        for event in events:
            event_time_sec = event['time_sec']
            delta_sec = event_time_sec - last_event_time_sec
            delta_ticks = int(np.round(delta_sec * self.ticks_per_sec))

            if event['type'] == 'note_on':
                track.append(mido.Message('note_on', note=event['note'], velocity=64, time=delta_ticks)) # közepes hangerővel hozzuk létre
            else:
                track.append(mido.Message('note_off', note=event['note'], velocity=64, time=delta_ticks))

            last_event_time_sec = event_time_sec # frissítjük az utolsó esemény idejét

        try:
            mid.save(output)
            print(f"MIDI fájl sikeresen elmentve: {output}")
        except Exception as e:
            print(f"Hiba a MIDI fájl mentésekor: {e}")

