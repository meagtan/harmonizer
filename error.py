# Computing the error rate of the harmonizer

from harmonize import *
import random

# TODO also test key
def errorrate(sample):
    'Calculate the error rate of the algorithm over the given sample.'
    p = Freq() # frequency table for whether a classification is correct or incorrect
    for v in voices(sample):
        cs = harmonize(list(sample.notes(v)), sample.key, v)[1]
        for c, c1 in zip(sample.chords(), cs):
            p[c == c1] += 1
    return p[True, False] # probability of failure

def kfoldcv(samples = None, k = 10):
    'Run k-fold cross-validation on set of samples, .'
    global table
    t = table # back up original table
    if not samples:
        samples = list(table.samples)
    
    # shuffle samples randomly, to partition into k random blocks
    random.shuffle(samples)
    
    # train table k times
    err = 0
    n = len(samples) / k
    for i in xrange(k+1): # k+1 to include rounding down
        table = freqs.Env()
        table.train(samples[:i*n] + samples[(i+1)*n:])
        err += sum(errorrate(sample) for sample in samples[i*n:(i+1)*n])
    table = t
    return err / len(samples)

def voices(sample):
    'Return the intersection of the voices of all chords in a given sample.'
    return xrange(min(len(c.pitches) for c in sample.chords()))
