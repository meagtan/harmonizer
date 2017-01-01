import freqs
import heapq as hp
from collections import defaultdict

table = freqs.Env()

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
    c, k = best
    chors = [c]
    for i in xrange(length - 1, 0, -1):
        c = preds[c, k, i]
        chors.append(c)
    
    return k, chors, bestprob
    
#   # Dijkstra's algorithm, modified to change (min,+) into (max,*) for distances
#   openset = []
#   probs   = {}
#   preds   = {}
#   length  = len(notes)
#   
#   for c in chords(notes[0]):
#       for k in [key] if key else keys:
#           probs[0, c, k] = cprob(c, k) * nprob(notes[0], c, k, voice)
#           hp.heappush(openset, (-probs[0, c, k], (0, c, k))) # negative for max heap
#   
#   while openset:
#       i, c, k = hp.heappop(openset)[1]
#       
#       # found likeliest complete sequence
#       if i == length - 1: 
#           res = []
#           while (i, c, k) in preds:
#               res.append(c)
#               i, c, k = preds[i, c, k]
#           res.append(c)
#           res.reverse()
#           return k, res 
#       
#       for c1 in chords(notes[i+1]):
#           newprob = probs[i, c, k] * cprob(c1, k, c, vel) * nprob(notes[i+1], c1, k, voice, notes[i], c, vel)
#           newitem = (i + 1, c1, k)
#           if newitem not in probs or newprob > probs[newitem]:
#               probs[newitem] = newprob
#               preds[newitem] = i, c, k
#               hp.heappush(openset, (-newprob, newitem))
#   return None

def cprob(c, k, c1 = None, vel = None):
    '''
    cprob(c, k, c1 = None, vel = None)
    Returns the probability that chord c will occur in key k, optionally after chord c1 and with harmonic velocity vel.
    '''
    # compute P(Trans(Func(c, k), Func(c1, k))[| vel])
    # TODO normalize over None variables instead, or move that to freqs
    if not c1 or not vel:
        return table.cprob(c, k)
    return table.tprob(c, k, c1, vel)

def nprob(n, c, k, voice = None, n1 = None, c1 = None, vel = None):
    '''
    nprob(n, c, k, voice = None, n1 = None, c1 = None, vel = None)
    Returns the probability that note n will occur in the given voice of chord c and key k, 
    optionally after note n1 in chord c1 and with harmonic velocity vel.
    '''
    # compute P(Pitch(n, c) | Pitch(n1, c1), voice, Trans(Func(c1, k), Func(c, k)), vel)
    if not n1 or not c1 or not vel:
        return table.nprob(n, c, k, voice)
    return table.vprob(n, n1, c, c1, k, voice, vel)

def chords(note, key = None, voice = None):
    '''
    chords(note, key = None, voice = None)
    Iterates through all chords that contain note, optionally in a given key or voice.
    Returns a generator of tuples of type (Chord, Key, Probability).
    '''
    # probability = cprob(chord, key) * nprob(note, chord, key, voice)
    def prob(c, n, k, v):
        return cprob(c, k) * nprob(n, c, k, v)
    
    for k in ([key] if key else keys): # TODO keys list
        for c in chords: # TODO chords list
            p = prob(c, note, key, voice)
            if p > threshold: # TODO constant threshold
                yield c, k, p