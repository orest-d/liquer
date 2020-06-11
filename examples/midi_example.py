import sys
sys.path.append("..")

import pandas as pd
from liquer import *
import liquer.ext.basic
import liquer.ext.midi
import liquer.ext.lq_pandas


@first_command
def pentatonic():
    sequence = [61,63,66,68,70]
    df = pd.DataFrame(columns=["time", "pitch", "duration", "volume"])
    for t,x in enumerate(sequence):
        df = df.append(dict(time=t, pitch=x, duration=1, volume=100), ignore_index=True)
    return df
    

evaluate_and_save("ns-midi/pentatonic/df_as_midi/pentatonic.mid")