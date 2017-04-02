### Histogram analysis for easier recognition of keys, chords, themes, etc.

import freqs
from music21 import pitch
from math import log
from svmutil import * # for keysvm, requires libsvm

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

# Other histogram-based classifiers against which to measure the accuracy of findkey

def findkeyks(s):
    'Return the most likely key of a sample, using the Krumhansl-Schmuckler algorithm.'
    return s.cs.analyze('krumhansl')

class keysvm():
    'SVM classifier for finding the most likely key of a sample from its histogram.'
    
    def __init__(self, samples):
        'Train SVM from given set of samples.'
        x, y = [], []
        for s in samples:
            h = histogram(s)
            y.append(freqs.keys.index(s.key)) # labels of multi-class classifier correspond to indices of keys
            x.append(dict((freqs.tones.index(str(n)), h[n]) for n in h)) # each dimension corresponds to the index of a note
        prob = svm_problem(y, x)
        param = svm_parameter('-t 0 -v 5 -q')
        self.m = libsvm.svm_train(prob, param)
    
    def findkey(self, s):
        'Predict the key of a sample based on the trained SVM classifier.'
        h = histogram(s)
        x0, _ = gen_svm_nodearray(dict((freqs.tones.index(str(n)), h[n]) for n in h)) # TODO make this into a function
        return freqs.keys[int(libsvm.svm_predict(self.m, x0))]
