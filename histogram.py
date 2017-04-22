### Histogram analysis for easier recognition of keys, chords, themes, etc.

import freqs
from music21 import *
from math import *
from svmutil import * # for keysvm, requires libsvm
from operator import concat

def findkey(table, s):
    'Return the most likely key of a sample, given probability table.'
    return max(freqs.keys, key = lambda k: loglikelihood(table, s, k))

def loglikelihood(table, s, k):
    'Return the log-likelihood of a sample being in a particular key.'
    h = histogram(s)
    return sum(log(table.nfreq[True, freqs.Tone(n, k)]) * h[n] for n in h) + log(table.kprob(k))

def histogram(s):
    'Construct a pitch histogram for a sample.'
    h = freqs.Freq()
    for c in s: # TODO make s iterable, also implement len, indexing, etc.
        for n in c.pitches:
            h[pitch.Pitch(n.name), n.octave] += 1 # separate octave from pitch
    return h

# Other histogram-based classifiers against which to measure the accuracy of findkey

def findkeyks(s):
    'Return the most likely key of a sample, using the Krumhansl-Schmuckler algorithm.'
    return s.cs.analyze('krumhansl')

# too many classes, may overfit, does not consider permutations of the same vector
class keysvm():
    'SVM classifier for finding the most likely key of a sample from its histogram.'
    
    def __init__(self, samples):
        'Train SVM from given set of samples.'
        x, y = [], []
        for s in samples:
            h = histogram(s)
            y.append(freqs.keys.index(s.key)) # labels of multi-class classifier correspond to indices of keys
            x.append(histtodict(h)) # each dimension corresponds to the index of a note
        prob = svm_problem(y, x)
        param = svm_parameter('-t 0 -v 5 -q')
        self.m = libsvm.svm_train(prob, param)
    
    def findkey(self, s):
        'Predict the key of a sample based on the trained SVM classifier.'
        h = histogram(s)
        x0, _ = gen_svm_nodearray(histtodict(h))
        return freqs.keys[int(libsvm.svm_predict(self.m, x0))]

# too many false negatives, perhaps combine approach with keysvm
class keysvm2():
    "Two-class SVM classifier classifying a histogram correctly if it's measured from the tonic and incorrectly otherwise."
    
    def __init__(self, samples):
        'Train SVM from given set of samples.'
        x, y = [], []
        for s in samples:
            h = histogram(s)
            # for each key, classify as positive if measured from the tonic and negative otherwise
            for i, k in enumerate(freqs.keys):
                if k.tonic in h: # preventative measure to eliminate too many negatives
                    y.append(1 if k == s.key else -1) # correct iff measured from tonic
                    x.append(histtodict(h, i)) # measure distance of notes to key
        prob = svm_problem(y, x)
        param = svm_parameter('-t 1 -d 2 -v 5 -q') # quadratic kernel, in order to accept positive cone
        self.m = libsvm.svm_train(prob, param)
    
    def findkey(self, s):
        'Predict the key of a sample based on the trained SVM classifier.'
        h = histogram(s)
        for i, k in enumerate(freqs.keys):
            x0, _ = gen_svm_nodearray(histtodict(h, i))
            if libsvm.svm_predict(self.m, x0) > 0:
                yield k

def histtodict(h, i = 0):
    'Convert histogram to dictionary with numeric keys, optionally with offset.'
    return dict(((freqs.tones.index(str(n)) - i) % len(freqs.tones), h[n]) for n in h)
