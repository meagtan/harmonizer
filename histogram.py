### Histogram analysis for easier recognition of keys, chords, themes, etc.

import freqs
from music21 import pitch
from math import log

def findkey(table, s):
    'Return the most likely key of a sample, given probability table.'
    h = histogram(s)
    return max(freqs.keys, key = lambda k: sum(log(table.nfreq[True, freqs.Tone(n, k)]) * h[n] for n in h))

def histogram(s):
    'Construct a pitch histogram for a sample.'
    h = freqs.Freq()
    for c in s.chords():
        for n in c.pitches:
            h[pitch.Pitch(n.name), n.octave] += 1 # separate octave from pitch
    return h
