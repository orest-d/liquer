import sys
sys.path.append("..")

import pandas as pd
from liquer import *
import liquer.ext.basic
import liquer.ext.lq_pandas

from midiutil import MIDIFile
from io import BytesIO


@command(ns="midi")
def df_as_midi(df, tempo=120):
    """Converter dataframe to midi file expects columns time, pitchN, durationN, volumeN
    for N=0...15 (0 should be omitted)
    """
    track = 0
    time = df.time if "time" in df.columns else range(len(df))

    MyMIDI = MIDIFile(1)
    MyMIDI.addTempo(track, 0, tempo)

    for i, row in df.iterrows():
        t = time[i]
        for channel in range(15):
            N = "" if channel == 0 else str(channel)
            if f"pitch{N}" in df.columns:
                pitch = row[f"pitch{N}"]
                if pitch is not None:
                    duration = row[f"duration{N}"] if f"duration{N}" in row else 1
                    volume = row[f"volume{N}"] if f"volume{N}" in row else 100
                    MyMIDI.addNote(
                        track, channel, int(pitch), int(t), int(duration), int(volume)
                    )

    f = BytesIO()
    MyMIDI.writeFile(f)
    return f.getvalue()


@first_command
def pentatonic():
    sequence = [61,63,66,68,70]
    df = pd.DataFrame(columns=["time", "pitch", "duration", "volume"])
    for t,x in enumerate(sequence):
        df = df.append(dict(time=t, pitch=x, duration=1, volume=100), ignore_index=True)
    return df
    

evaluate_and_save("ns-midi/pentatonic/df_as_midi/pentatonic.mid", target_directory=".")