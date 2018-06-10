### Vectorized equivalents of freqs, frequtils, etc.

from music21 import *
import numpy as np

tones = [n + a for n in 'CDEFGABcdefgab' for a in ['-', '#', '']]
keys = map(key.Key, tones)
chords = [chord.Chord(map(k.pitches.__getitem__, [0, 2, 4])) for k in keys]
notes = [n for n in tones if isupper(n[0])]
K, C, N = len(keys), len(chords), len(notes)

F = 7*5*4*2
T = 7*5

# vectorize these

def Func(chord, key):
    try:
        num = (chord.root().diatonicNoteNum - key.tonic.diatonicNoteNum) % 7
        acc = (chord.root().ps - key.pitches[num].ps + 2) % 12 # assuming only 5 different types of accidentals occur
        
        return np.ravel_multi_index((num, acc, chord.quality, key.mode), (7, 5, 4, 2)) # TODO take care of other qualities
    except AttributeError:
        return ()

def Tone(note, key):
    try:
        num = (note.diatonicNoteNum - key.tonic.diatonicNoteNum) % 7
        acc = (note.ps - key.pitches[num].ps + 2) % 12
        return np.ravel_multi_index((num, acc), (7, 5)) # store accidental
    except AttributeError:
        return ()

class Sample:
    '''
    A processed sample chorale containing a list of chords, with optionally specified harmonic velocity.
    '''
    def __init__(self, filename):
        self.filename = filename
        self.s = converter.parse(filename)
        # self.cs = self.s.chordify()
        
        self.key = self.s.analyze('krumhansl')
        self.vel = None # TODO change this, perhaps use qualities other than vel, such as measure ends
        self.matrix = None
        
    # TODO function converting sample into TxN matrix of notes + Tx1 array of absolute durations
    def get_matrix(self):
        if self.matrix is None:
            # TODO create matrix
            # do not use Func and Tone, instead store absolute note values
            # likelihoods however should use them for symmetry
            pass
        return self.matrix
    
    def measures(self):
        'Iterates through each measure of sample.'
        for m in self.cs:
            if isinstance(m, stream.Measure):
                yield m
    
    def chords(self):
        'Iterates through each chord of sample.'
        for m in self.measures():
            for c in m.notes: # cannot call notes directly apparently
                yield c
    
    def notes(self, voice):
        'Iterates through each note in sample at a given voice.'
        for p in self.s.parts[voice]:
            for m in p.getElementsByClass('Measure'):
                for n in m.notes:
                    yield n
    
    # iterable overrides, may be made more efficient
    def __iter__(self):
        return self.chords()
    def __len__(self):
        return len(self.cs)
    def __getitem__(self, key):
        return list(self.chords())[key] # can also take slice objects
    
    def __hash__(self):
        return hash(self.filename)
    def __eq__(self, other):
        return isinstance(other, Sample) and self.filename == other.filename
    def __ne__(self, other):
        return not self.__eq__(other)
   
    pass

class Stats:
    '''
    Stores counts of chords, notes, transitions, etc.
    '''
    def __init__(self, sample=None):
        self.cs = np.ndarray((C,))
        self.ts = np.ndarray((C,C))
        self.ns = np.ndarray((N,))
        self.vs = np.ndarray((N,N))
        self.ks = np.ndarray((K,))
        
        if sample is not None:
            # TODO construct stats from sample matrix
            pass
        
    def __add__(self, other):
        res = Stats()
        res.cs = self.cs + other.cs
        res.ts = self.ts + other.ts
        res.hs = self.hs + other.hs
        res.vs = self.vs + other.vs
        res.ks = self.ks + other.ks
        return res
    
    def __radd__(self, other):
        return other.__add__(self)
    
    # add methods returning NxK etc. probability matrices looking up entries for Tone(n,k) etc.

class Env:
    '''
    Program environment containing probabilities for each chord, note and transition, acquired from sample chord sequences.
    '''
    def __init__(self):
        self.stats = Stats()
        self.samples = dict()
    
    def train(self, filenames):
        'Train probabilities from given iterator of filenames, for example corpus.getBachChorales().'
        for f in filenames:
            s = Sample(f)
            if s not in self.samples:
                print 'Processing %s...' % f
                self.process(s)
    
    def process(self, sample):
        'Update probabilities based on a sample sequence of chords.'
        if sample in self.samples:
            return
        
        # construct Stats from Sample
        # may also look at small windows in sample
        self.samples[sample] = Stats(sample)
        self.stats += self.samples[sample]
    
    # TODO fill these below, or move some to Stats
    
    def kprob(self, k):
        'kprob(k) -> Return probability of key k.'
        return (self.stats.ks[k]+1) / (self.stats.ks+1).sum()
    
    def cprob(self, c, k):
        'cprob(c, k) -> Return probability of chord c occurring in key k.'
        return self.cfreq[True, Func(c, k)]
    
    def nprob(self, n, c, k, v = None):
        'nprob(n, c, k[, v]) -> Return probability of note n occurring in voice v of chord c in key k.'
        return self.nfreq[True, Tone(n, k), k.mode, Func(c, k), v] # should normalize over v if not none
    
    def tprob(self, c1, c, k, vel = None):
        'tprob(c1, c, k[, vel]) -> Return probability of chord c changing to chord c1 in key k under harmonic velocity vel.'
        if c == c1:
            return self.cprob(c, k) # perhaps dependent on vel
        f, f1 = Func(c, k), Func(c1, k)
        return self.tfreq[True, f1, f, s]
    
    def vprob(self, n1, n, c1, c, k, v = None, vel = None):
        '''vprob(n1, n, c1, c, k[, v, vel]) -> 
        Return probability of note n in chord c changing to note n1 in chord c1 
        in key k and voice v under harmonic velocity vel.'''
        if n == n1 and c == c1:
            return self.nprob(n, c, k, v) # perhaps dependent on vel
        f, f1 = Func(c, k), Func(c1, k)
        t, t1 = Tone(n, k), Tone(n1, k)
        return self.vfreq[True, t1, t, f1, f, v, s]
    
table = Env()