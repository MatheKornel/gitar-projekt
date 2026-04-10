import mido
import numpy as np
from quantizing import Quantizing

class MidiExporter:
    def __init__(self, ppqn=480, tempo=120):
        self.ppqn = ppqn # Pulses Per Quarter Note
        self.tempo = tempo # BPM
        self.sec_per_beat = 60 / self.tempo
    
    def create_midi(self, notes, output="output.mid"):
        mid = mido.MidiFile(ticks_per_beat=self.ppqn)
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # tempó beállítása
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(self.tempo)))

        quantizer = Quantizing(notes)

        # esemény lista -- minden hanghoz tartozik note_on és note_off esemény
        events = []
        for i, note_event in enumerate(notes):
            quant_onset, quant_offset = quantizer.quantize(note_event, i, self.sec_per_beat)

            onset_ticks = int(round(quant_onset * self.ppqn))
            offset_ticks = int(round(quant_offset * self.ppqn))

            events.append({'time_ticks': onset_ticks, 'type': 'note_on', 'note': note_event.midi_note, 'velocity': note_event.velocity})
            events.append({'time_ticks': offset_ticks, 'type': 'note_off', 'note': note_event.midi_note, 'velocity': note_event.velocity})
        
        events.sort(key=lambda x: (x['time_ticks'], x['type'])) # időrendbe rendezés

        # események hozzáadása a MIDI trackhez delta idővel
        last_event_time_sec = 0.0
        for event in events:
            delta_ticks = event['time_ticks'] - last_event_time_sec
            delta_ticks = 0 if delta_ticks < 0 else delta_ticks

            if event['type'] == 'note_on':
                track.append(mido.Message('note_on', note=event['note'], velocity=64, time=int(delta_ticks))) # közepes hangerővel hozzuk létre
            else:
                track.append(mido.Message('note_off', note=event['note'], velocity=64, time=int(delta_ticks)))

            last_event_time_sec = event['time_ticks'] # frissítjük az utolsó esemény idejét

        try:
            mid.save(output)
            print(f"MIDI fájl sikeresen elmentve: {output}")
        except Exception as e:
            print(f"Hiba a MIDI fájl mentésekor: {e}")

