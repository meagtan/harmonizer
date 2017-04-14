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
    c = [1] * n # c[r] corresponds to the class weight of region r
    m = [1] * n # m[r] corresponds to the class mean of region r
    k = [1] * n # k[r] corresponds to the most likely key for region r
    v = 1  # v is the common class variance, initially irrelevant and set to 1
    ms = list(m.notes for m in s.cs if isinstance(m, stream.Measure) # list of measures, simplify late
    l = len(ms) # total duration of sample
    km = findkey(table, s) # key of whole piece
    
    # initially, divide sample evenly
    for r in xrange(n):
        m[r] = (r + 0.5) * l / n
    
    # loop until convergence
    for _ in xrange(10): # TODO better condition, such as regions not changing
        # find b[r] from c[r] and m[r]
        b = boundaries(c, m, v, l)
        for r in b:
            # calculate k[r] from b[r]
            k[r] = findkey(table, reduce(concat, ms[b[r][0]:b[r][1]])) # or perhaps compute k[r] from matrix product of s and w
        # calculate weights
        for t in xrange(l):
            rs = dict((r, exp(-(t-m[r]) ** 2 / v + log(c[r]) + loglikelihood(table, ms[t], k[r]))) for r in b)
            rm = max(rs, lambda r: rs[r])
            # rsum = sum(rs[r] for r in rs)
            for r in b:
                w[t, r] = float(r == rm) # approximation for rs[r] / rsum
        # update parameters
        for r in b:
            c[r] = sum(w[t,r] for t, r1 in w if r == r1) / sum(w[t,r1] for t, r1 in w if r in b)
            m[r] = sum(t * w[t,r] for t, r1 in w if r == r1) / sum(w[t,r] for t, r1 in w if r == r1)
            v = sum((t - m[r]) ** 2 * w[t,r1] for t, r1 in w if r in b) / sum(w[t,r] for t, r1 in w if r == r1)
    return boundaries(c, m, v, l)

def boundaries(c, m, s, l):
    'Calculate region boundaries from region means and weights.'
    def discr(t, r):
        'Linear discriminant for classifying a time instant to a region.'
        return 2 * m[r] * t - m[r] ** 2 + s ** 2 * log(c[r])
    def intersect(r, r1):
        'The time the discriminants of two different regions intersect.'
        # 2(m[r]-m[r1])t - m[r]^2 + m[r1]^2 + s^2 log(c[r]/c[r1]) = 0
        return (m[r] + m[r1]) / 2 - s ** 2 * log(c[r]/c[r1]) / (2 * (m[r] - m[r1]))
    b = {}
    t = 0
    n = len(c)
    
    # find most likely region in the beginning, hopefully region 0
    r = max(xrange(n), key = lambda r: discr(t, r))
    while t < l:
        # find the region first to overcome the discriminant of the current region and set it to the next region
        # perhaps optimize this through dynamic programming
        try:
            t1, r1 = min(((intersect(r, r1), r1) for r1 in xrange(n) if r != r1 and intersect(r, r1) > t))
        except ValueError: # empty iterator
            t1, r1 = l, r
        b[r] = t, t1
        r, t = r1, t1
    return b
