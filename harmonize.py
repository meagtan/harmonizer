import freqs
import heapq as hp
from collections import defaultdict
from music21 import corpus
from frequtils import *

table = freqs.table

def harmonize(notes, key = None, voice = None, vel = None): # TODO generalize as kwargs
    '''
    harmonize(notes, key = None, voice = None, vel = None)
    Returns the most probable sequence of chords for the given sequence of notes, with optional information
    given for the key, voice, signature and harmonic rhythm.
    The key is inferred if not provided; the other variables are averaged or not considered.
    '''
    
    # Viterbi algorithm
    probs  = defaultdict(Prob)
    preds  = {}
    length = len(notes)
    
    for c, k, p in chords(notes[0], key, voice): # should iterate through all keys if key None, else just k
        probs[c, k, 0] = p # cprob(c, k) * nprob(notes[0], c, k, voice) # perhaps move cprob to chords
    
    for i in xrange(1, length):
        bestprob = Prob()
        best = None
        for c, k, _ in chords(notes[i], key, voice):
            # find max and arg max of transition
            for c1, _ in chords(notes[i-1], k):
                newprob = probs[c1, k, i - 1] * cprob(c1, k, c, vel) * nprob(notes[i], c1, k, voice, notes[i-1], c, vel)
                if probs[c, k, i] < newprob:
                    probs[c, k, i] = newprob
                    preds[c, k, i] = c1
            # update bestprob and bestchor
            if bestprob < probs[c, k, i]:
                bestprob = probs[c, k, i]
                best = c, k
    
    # construct chords
    # perhaps construct likeliest four-part voice leading from these later
    c, k = best
    chors = [c]
    for i in xrange(length - 1, 0, -1):
        c = preds[c, k, i]
        chors.append(c)
    
    return k, chors, bestprob

def cprob(c, k, c1 = None, vel = None):
    '''
    cprob(c, k[, c1, vel])
    Returns the probability that chord c will occur in key k, optionally after chord c1 and with harmonic velocity vel.
    '''
    # compute P(Trans(Func(c, k), Func(c1, k))[| vel])
    # TODO normalize over None variables instead, or move that to freqs
    if not c1 or not vel:
        return table.cprob(c, k)
    return table.tprob(c, k, c1, vel)

def nprob(n, c, k, voice = None, n1 = None, c1 = None, vel = None):
    '''
    nprob(n, c, k[, voice, n1, c1, vel])
    Returns the probability that note n will occur in the given voice of chord c and key k, 
    optionally after note n1 in chord c1 and with harmonic velocity vel.
    '''
    # compute P(Pitch(n, c) | Pitch(n1, c1), voice, Trans(Func(c1, k), Func(c, k)), vel)
    if not n1 or not c1 or not vel:
        return table.nprob(n, c, k, voice)
    return table.vprob(n, n1, c, c1, k, voice, vel)

def chords(note, key = None, voice = None):
    '''
    chords(note[, key, voice])
    Iterates through all chords that contain note, optionally in a given key or voice.
    Returns a generator of tuples of type (Chord, Key, Probability).
    '''
    # probability = cprob(chord, key) * nprob(note, chord, key, voice)
    def prob(c, n, k, v):
        return cprob(c, k) * nprob(n, c, k, v)
    
    for k in ([key] if key else keys):
        for c in chords:
            p = prob(c, note, key, voice)
            if p > threshold: # TODO constant threshold
                yield c, k, p
