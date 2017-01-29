# Computing the error rate of the harmonizer

from harmonize import *

def error(sample):
    'Calculate the error rate of the algorithm over the given sample.'
    p = Freq() # frequency table for whether a classification is correct or incorrect
    for v in voices(sample): # TODO
        cs = harmonize(list(sample.notes(v)), sample.key, v)[1]
        for c, c1 in zip(sample.chords(), cs):
            p[c == c1] += 1
    return p[True, False] # probability of failure
