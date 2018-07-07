### Histogram analysis for easier recognition of keys, chords, themes, etc.

# TODO use arrays here

import numpy as np

import freqsarray as freqs 
from math import *

def findkey(table, s):
    'Return the most likely key of a sample, given probability table.'
    h = histogram(s)
    return max((loglikelihood(table, h, k), k) for k in freqs.keys)

def loglikelihood(table, h, k):
    'Return the log-likelihood of a histogram being in a particular key.'
    if not isinstance(h, freqs.Freq):
        h = histogram(h)
    return sum(log(table.nfreq[True, freqs.Tone(n, k)]) * h[n] for n in h) + log(table.kprob(k))

# TODO loglikelihood(table, hs) where hs.shape = (T,N) returning (T,K) matrix of probabilities
# just matrix multiplication by a matrix with (n,k) entry set to log p(n|k)

def histogram(s):
    'Construct a pitch histogram for a sample.'
    return s.get_matrix().sum(axis=0)

def logpnk(table):
    'Return KxN table storing ln p(n|k).'
    p = np.log(table.stats.ns + 1) - np.log((table.stats.ns+1).sum())
    return np.array([freqs.transpose_tone(p, k, False) for k in freqs.keys])

def logpcck(table):
    'Return KxCxC table storing ln p(c|c1,k).'
    
    pass

def logpnck(table):
    'Return KxCxN table storing ln p(n|c,k).'
    pass

def logpffm(table):
    'Return 2xFxF table storing ln p(f|f1,m) where m = minor,major.'
    pass

def logptfm(table):
    'Return 2xFxT table storing ln p(t|f,m) where m = minor,major.'
    pass

def findkeyks(s):
    'Return the most likely key of a sample, using the Krumhansl-Schmuckler algorithm.'
    return s.cs.analyze('krumhansl')

def histtodict(h, i = 0):
    'Convert histogram to dictionary with numeric keys, optionally with offset.'
    return dict(((freqs.tones.index(str(n)) - i) % len(freqs.tones), h[n]) for n in h)