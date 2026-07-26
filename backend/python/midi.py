import os

import mido

from config import ProjectPaths
from quantizing import Quantizing


class MidiExporter:
    def __init__(self, ppqn=480, tempo=120, paths: ProjectPaths | None = None):
        self.ppqn = ppqn
        self.tempo = tempo
        self.sec_per_beat = 60 / self.tempo
        self.paths = paths or ProjectPaths()

    def create_midi(self, notes, output="output.mid"):
        mid = mido.MidiFile(ticks_per_beat=self.ppqn)
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.tempo)))

        quantizer = Quantizing(notes)
        events = []
        for i, note_event in enumerate(notes):
            quant_onset, quant_offset = quantizer.quantize(note_event, i, self.sec_per_beat)

            onset_ticks = int(round(quant_onset * self.ppqn))
            offset_ticks = int(round(quant_offset * self.ppqn))

            events.append({"time_ticks": onset_ticks, "type": "note_on", "note": note_event.midi_note, "velocity": note_event.velocity})
            events.append({"time_ticks": offset_ticks, "type": "note_off", "note": note_event.midi_note, "velocity": note_event.velocity})

        events.sort(key=lambda x: (x["time_ticks"], x["type"]))

        last_event_time_ticks = 0
        for event in events:
            delta_ticks = max(0, event["time_ticks"] - last_event_time_ticks)
            if event["type"] == "note_on":
                track.append(mido.Message("note_on", note=event["note"], velocity=64, time=int(delta_ticks)))
            else:
                track.append(mido.Message("note_off", note=event["note"], velocity=64, time=int(delta_ticks)))
            last_event_time_ticks = event["time_ticks"]

        output_path = self.paths.output_path(output, kind="midi") if os.path.dirname(output) == "" else output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            mid.save(output_path)
            print(f"MIDI fájl sikeresen elmentve: {output_path}")
        except Exception as e:
            print(f"Hiba a MIDI fájl mentésekor: {e}")

