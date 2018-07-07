### Vectorized equivalents of freqs, frequtils, etc.

from music21 import *
import numpy as np

tones = [n + a for n in 'CDEFGABcdefgab' for a in ['-', '#', '']]
keys = map(key.Key, tones)
chords = [chord.Chord(map(k.pitches.__getitem__, [0, 2, 4])) for k in keys] # TODO does not include diminished
notes = [n for n in tones if n[0].isupper()]
K, C, N = len(keys), len(chords), len(notes)

C = F = 7*7*4
N = T = 7*7

# vectorize these
# may also use music21.roman later

def Func(chord, key=key.Key('C')):
    try:
        num = int(chord.root().diatonicNoteNum - key.tonic.diatonicNoteNum) % 7
        acc = int(chord.root().ps - key.pitches[num].ps + 3) % 12 # assuming only 5 different types of accidentals occur
        qual = ['major','minor','diminished','augmented', 'other'].index(chord.quality) % 4
        return np.ravel_multi_index((num, acc, qual), (7, 7, 4))
    except AttributeError:
        return -1

def Chord(func, key=key.Key('C')):
    num, acc, qual = np.unravel_index(func, (7,7,4))
    root = Pitch(np.ravel_multi_index((num, acc), (7, 7)), key)
    # TODO

def Tone(note, key=key.Key('C')): # if no key, use absolute value
    try:
        num = int(note.diatonicNoteNum - key.tonic.diatonicNoteNum) % 7
        acc = int(note.ps - key.pitches[num].ps + 3) % 12
        return np.ravel_multi_index((num, acc), (7, 7)) # store accidental
    except:
        return -1

def Pitch(tone, key=key.Key('C')):
    try:
        num, acc = np.unravel_index(tone, (7,7))
        p = key.pitches[num]
        return pitch.Pitch(p.name[0], accidental=p.alter+acc-3)
    except:
        return None

abs2func_tone = np.array([[Tone(Pitch(t, k)) for t in xrange(T)] for k in keys])
func2abs_tone = np.array([[Tone(Pitch(t), k) for t in xrange(T)] for k in keys])
def transpose_tone(hist, key, tofunc=True):
    'Transpose histogram of absolute tones to tones in a given key.'
    if tofunc:
        arr = abs2func_tone[keys.index(key)]
    else:
        arr = func2abs_tone[keys.index(key)]
    return hist[arr]*(arr!=-1)

# matrices converting absolute notes/chords to functions in a key
C = F
# chord2func = np.array([[np.arange(F)==Func(Chord(f, k)) for f in xrange(F)] for k in keys])
# func2chord = np.array([[np.arange(F)==Func(Chord(f), k) for f in xrange(F)] for k in keys])
# pitch2tone = np.array([[np.arange(T)==Tone(Pitch(t, k)) for t in xrange(T)] for k in keys])
# tone2pitch = np.array([[np.arange(T)==Tone(Pitch(t), k) for t in xrange(T)] for k in keys])


def Key(key):
    return keys.index(key)

class Sample:
    '''
    A processed sample chorale containing a list of chords, with optionally specified harmonic velocity.
    '''
    def __init__(self, filename, fromCorpus=False):
        self.filename = filename
        if fromCorpus:
            self.s = corpus.parse(filename)
        else:
            self.s = converter.parse(filename)
        # self.cs = self.s.flat.notesAndRests.stream().chordify()
        
        self.key = self.s.analyze('krumhansl')
        self.vel = None # TODO change this, perhaps use qualities other than vel, such as measure ends
        self.matrix = None
        
    # function converting sample into TxN matrix of notes + Tx1 array of absolute durations
    def get_matrix(self):
        if self.matrix is None:
            s = self.s.flat.notesAndRests.stream()
            endtimes = s._uniqueOffsetsAndEndTimes(endTimesOnly=True)
            l = len(endtimes)
            self.matrix = np.zeros((l,T))
            self.ts = np.zeros(l)
            t0 = 0
            for i, t in enumerate(endtimes):
                a = s.getElementsByOffset(t0, t, includeEndBoundary=False)
                for n in a:
                    if isinstance(n, chord.Chord):
                        for p in n.pitches:
                            self.matrix[i, Tone(p)] += t - t0
                    elif isinstance(n, note.Note):
                        self.matrix[i, Tone(n.pitch)] += t - t0
                self.ts[i] = (t0 + t)/2
                t0 = t
        return self.matrix, self.ts
    
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
        self.cs = np.zeros((2,C)) # np.zeros((C,))
        self.ts = np.zeros((2,F,F)) # np.zeros((C,C)) # no of transitions between each two functions, for each key mode
        self.ns = np.zeros((T,))
        self.es = np.zeros((2,T,F)) # instances of each tone in a chord, for each key mode
        self.vs = np.zeros((T,T))
        self.ks = np.zeros((K,))
        # self.ts = np.zeros((2,F,F)) # no of transitions between each two functions, for each key mode
        # self.ns = np.zeros((2,F,T)) # instances of each tone in a chord, for each key mode
        # self.cs may store initial chords for each key
        
        if sample is not None:
            # construct stats from sample matrix
            self.ks[Key(sample.key)] += 1
            # construct note histogram
            m = sample.get_matrix()[0]
            self.ns += transpose_tone(m.sum(axis=0), sample.key) # remove later
            # TODO handle the rest of the arrays
            c1 = None
            for t in xrange(m.shape[0]):
                # infer which chord is active
                notes = [Pitch(n) for n in m[t].nonzero()[0]]
                if len(notes) == 0:
                    continue
                c = chord.Chord(notes)
                # if t % 50 == 0:
                #     print c, m[t].sum(), Func(c, sample.key), Chord(Func(c, sample.key), sample.key)
                if c1 is None:
                    self.cs[int(sample.key.mode == 'major'), Func(c,sample.key)] += m[t].sum()
                else: # may distribute 'other' chords to every other mode
                    self.ts[int(sample.key.mode == 'major'), Func(c1,sample.key), Func(c,sample.key)] += m[t].sum() 
                for n in notes:
                    self.es[int(sample.key.mode == 'major'), Tone(n,sample.key), Func(c,sample.key)] += m[t,Tone(n)]
                c1 = c
   
    def __add__(self, other):
        res = Stats()
        res.cs = self.cs + other.cs
        res.ts = self.ts + other.ts
        res.ns = self.ns + other.ns
        res.vs = self.vs + other.vs
        res.es = self.es + other.es
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
    
    def train(self, filenames, verbose=False):
        'Train probabilities from given iterator of filenames, for example corpus.getBachChorales().'
        for f in filenames:
            s = Sample(f)
            if s not in self.samples:
                if verbose:
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