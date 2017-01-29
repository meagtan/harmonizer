# Computing the error rate of the harmonizer

from harmonize import *

def error(sample):
    'Calculate the error rate of the algorithm over the given sample.'
    p = Freq() # frequency table for whether a classification is correct or incorrect
    for v in voices(sample):
        cs = harmonize(list(sample.notes(v)), sample.key, v)[1]
        for c, c1 in zip(sample.chords(), cs):
            p[c == c1] += 1
    return p[True, False] # probability of failure

def voices(sample):
    'Return the intersection of the voices of all chords in a given sample.'
    return xrange(min(len(c.pitches) for c in sample.chords()))
