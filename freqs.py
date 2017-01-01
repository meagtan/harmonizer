import music21
from fractions import Fraction

class Prob(Fraction):
    '''
    Integral type with extra normalization factor, to represent probabilities accurately.
    '''
    def __new__(cls, val = 0, norm = None):
        self = Fraction.__new__(cls, val if norm is None else Fraction(val, norm) if norm else 0)
        return self
    
    def __repr__(self):
        return self.__str__()
    
    # cast arithmetic operators
    def __add__(self, other):
        return Prob(Fraction.__add__(self, other))
    def __radd__(self, other):
        return Prob(Fraction.__radd__(self, other))
    def __sub__(self, other):
        return Prob(Fraction.__sub__(self, other))
    def __rsub__(self, other):
        return Prob(Fraction.__rsub__(self, other))
    def __mul__(self, other):
        return Prob(Fraction.__mul__(self, other))
    def __rmul__(self, other):
        return Prob(Fraction.__rmul__(self, other))
    
    # modify division for 0
    def __div__(self, other):
        return Fraction.__div__(self, other) if other != 0 else 0
    def __rdiv__(self, other):
        return Prob(other) / self

class Freq:
    '''
    Multiple dimensional frequency table.
    '''
    def __init__(self):
        self.table = {None : Prob(0)}
    
    def __getitem__(self, item, norm = True): 
        if norm:
            return Prob(self.__getitem__(item, False), self.table[None])
        try:
            if not item:
                return self.table[None]
            if not isinstance(item, tuple):
                return self.table[item][None]
            if item[0]:
                return self.table[item[0]].__getitem__(item[1:], False)
            return sum(self.table[i].__getitem__(item[1:], False) for i in self.table if i)
        except KeyError:
            return 0
    
    def __setitem__(self, item, value):
        self.table[None] += value - self.__getitem__(item, False) # should behave as assignment if item is None
        if item:
            if not isinstance(item, tuple):
                if item not in self.table:
                    self.table[item] = Freq()
                self.table[item][None] = value
            elif item[0]:
                if item[0] not in self.table:
                    self.table[item[0]] = Freq()
                self.table[item[0]][item[1:]] = value
    
    def __index__(self):
        return self.table[None]
    def __int__(self):
        return self.table[None]
    
class Env:
    '''
    Program environment containing probabilities for each chord, note and transition, acquired from sample chorales.
    '''
    def __init__(self):
        # Frequency tables
        self.cfreq = Freq() # freqs of each chord function
        self.tfreq = Freq() # freqs of each chord transition
        self.nfreq = Freq() # freqs of each note function in each chord function
        self.vfreq = Freq() # freqs of each note transition
        # TODO process every sample, or write a method for it
    
    def process(self, sample):
        'Update probabilities based on sample sequence of chords.'
        cs = sample.funcs()
        for curr, prev in zip(cs, [None] + cs[1:]):
            self.cfreq[curr, sample] += 1       
            self.tfreq[curr, prev, sample] += 1 
            for voice in voices(curr):
                # TODO note(chord, voice) returns note of chord in voice
                self.nfreq[note(curr, voice), curr, voice, sample] += 1
                self.vfreq[note(curr, voice), note(pred, voice), curr, pred, voice, sample] += 1
    
    # TODO memoize the following
    
    def cprob(self, c, k):
        'cprob(c, k) -> Return probability of chord c occurring in key k.'
        return self.cfreq[Func(c, k)]
    
    def nprob(self, n, c, k, v = None):
        'nprob(n, c, k[, v]) -> Return probability of note n occurring in voice v of chord c in key k.'
        return self.nfreq[Tone(n, c), Func(c, k), v] / self.cprob(c, k)
    
    def tprob(self, c1, c, k, vel = None):
        'tprob(c1, c, k[, vel]) -> Return probability of chord c changing to chord c1 in key k under harmonic velocity vel.'
        f, f1 = Func(c, k), Func(c1, k)
        return sum(self.tfreq[f1, f, s] / self.cfreq[f, s] for s in samples(vel)) # TODO normalize over f1
    
    def vprob(self, n1, n, c1, c, k, v = None, vel = None):
        '''vprob(n1, n, c1, c, k[, v, vel]) -> 
        Return probability of note n in chord c changing to note n1 in chord c1 
        in key k and voice v under harmonic velocity vel.'''
        f, f1 = Func(c, k), Func(c1, k)
        t, t1 = Tone(n, f), Tone(n1, f1)
        return sum(self.vfreq[t1, t, f1, f, v, s] * self.cfreq[f, s] / (self.nfreq[t, f, v, s] * self.tfreq[f1, f, s]) 
                   for s in samples(vel))
    
    def samples(self, vel = None):
        pass

class Func(int):
    '''
    Stores the diatonic function of a chord in a key, e.g. Func(A7, Dm) represents dominant major in a minor key.
    '''
    def __new__(cls, chord, key):
        self = int.__new__(cls, (chord.root().diatonicNoteNum - key.tonic.diatonicNoteNum) % 7 + 1)
        self.mod = chord.quality, key.mode
        return self
    pass

class Tone(int):
    '''
    Stores the tone of a note in a chord, e.g. Tone(C, DM) returns 7.
    '''
    def __new__(cls, note, func):
        self = int.__new__(cls, (note.diatonicNoteNum - chord.root().diatonicNoteNum) % 7 + 1)
        return self
    pass

class Sample:
    '''
    A processed sample chorale containing a list of chords, with optionally specified harmonic velocity.
    '''
    def funcs(self):
        'Return list of chord functions in sample.'
        pass
    pass
