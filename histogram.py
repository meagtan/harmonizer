### Histogram analysis for easier recognition of keys, chords, themes, etc.

import freqs
from music21 import pitch
from math import *
from svmutil import * # for keysvm, requires libsvm

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



## Recognizing modulation using EM
# The goal is to separate a piece of music into k regions such that each region is in a different key.
# P(r|(n_t)) ~ P(r) P(t|r) sum(P(k|r) P(n_t|t, k), k) ≈ P(r) P(t|r) P(n_t|t, k_max)
# P(t|r) is approximated as a normal distribution with variable mean but common variance.
# The region boundaries are controlled by the region means and weights, which provides cleaner and wider decision boundaries.
# The most likely key within a region is optimized by looking at the histogram of the region.

def modulation(table, s, n):
    '''
    Identify modulation in a sample s by dividing it into at most n regions.
    '''
    w = {} # w[t, r] corresponds to the weight of time t for region r
    c = [] # c[r] corresponds to the class weight of region r
    m = [] # m[r] corresponds to the class mean of region r
    k = [] # k[r] corresponds to the most likely key for region r
    b = [] # b[r] corresponds to the boundaries of region r
    s = 1  # s is the common class variance, initially set to 1
    l = len(s.cs) # total duration of sample
    km = findkey(table, s) # key of whole piece
    
    # initially, divide sample evenly
    for r in xrange(n):
        c[r] = 1
        m[r] = (r + 0.5) * l / n
    
    # loop until convergence
    for _ in xrange(10): # TODO better condition
        # find b[r] from c[r] and m[r]
        b = boundaries(c, m)
        for r in xrange(n):
            # calculate k[r] from b[r]
            k[r] = findkey(table, s[b[r][0]:b[r][1]]) # TODO implement slicing for Sample
            # calculate weights
            for t in xrange(l):
                w[t, r] = c[r] * exp(-((t-m[r])/s) ** 2 + loglikelihood(table, s[t:t+1], k[r]) - loglikelihood(table, s[t:t+1], km))
            # update parameters
            c[r] = sum(w[t,r] for t, r1 in w if r == r1) / sum(w[t,r1] for t, r1 in w)
            m[r] = sum(t * w[t,r] for t, r1 in w if r == r1) / sum(w[t,r] for t, r1 in w if r == r1)
            m1 = sum(t * w[t,r1] for t, r1 in w) / sum(w[t,r1] for t, r1 in w) # sample mean
            s = sum((t - m1) ** 2 * w[t,r1] for t, r1 in w) / sum(w[t,r] for t, r1 in w)
    return boundaries(c, m)

def boundaries(c, m):
    'Calculate region boundaries from region means and weights.'
    pass
