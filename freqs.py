from music21     import *
from collections import defaultdict
from frequtils   import *

class Freq:
    '''
    Multiple dimensional frequency table.
    '''
    def __init__(self):
        self.table = {None : 0}
    
    def __getitem__(self, item, norm = True): 
        if norm:
            return Prob(self.__getitem__(item, False), self.table[None])
        try:
            if item is None or item is (): # not item:
                return self.table[None]
            if not isinstance(item, tuple):
                return self.table[item][None]
            if item[0] is not None:
                return self.table[item[0]].__getitem__(item[1:], False)
            return sum(self.table[i].__getitem__(item[1:], False) for i in self.table if i)
        except KeyError:
            return 0 # or perhaps return sum (expected value?), to estimate unknown qualities using average [change to None for that]
    
    def __setitem__(self, item, value):
        self.table[None] += value - self.__getitem__(item, False) # should behave as assignment if item is None
        if item is not None and item is not (): # item:
            if not isinstance(item, tuple):
                if item not in self.table:
                    self.table[item] = Freq()
                self.table[item][None] = value
            elif item[0] is not None:
                if item[0] not in self.table:
                    self.table[item[0]] = Freq()
                self.table[item[0]][item[1:]] = value
    
    def __index__(self):
        return self.table[None]
    def __int__(self):
        return self.table[None]
    
class Env:
    '''
    Program environment containing probabilities for each chord, note and transition, acquired from sample chord sequences.
    '''
    def __init__(self):
        # Frequency tables    Properties tabulated                  Argument types (current always precedes previous)
        self.cfreq = Freq() # chord function                        Func, Sample
        self.tfreq = Freq() # chord transition                      Func, Func, Sample
        self.nfreq = Freq() # note function in each chord function  Tone, Func, Voice, Sample
        self.vfreq = Freq() # note transition                       Tone, Tone, Func, Func, Voice, Sample
        self.samples = defaultdict(set)
    
    def train(self, filenames):
        'Train probabilities from given iterator of filenames, for example corpus.getBachChorales().'
        for f in filenames:
            self.process(Sample(f))
    
    def process(self, sample):
        'Update probabilities based on a sample sequence of chords.'
        if sample in self.samples[None]:
            return
        
        vel = sample.vel
        key = sample.key
        
        # add sample to samples
        self.samples[None].add(sample)
        if vel:
            self.samples[vel].add(sample)
        
        prev = None
        for curr in sample.chords():
            f, f1 = Func(curr, key), Func(prev, key) # TODO prev is initially None
            self.cfreq[f, sample] += 1       
            self.tfreq[f, f1, sample] += 1 
            for voice, n in enumerate(chord, pitches):
                n1 = prev.pitches[voice] # what if multiple notes are played on the same chord? consider ties
                self.nfreq[n, f, voice, sample] += 1
                self.vfreq[n, n1, f, f1, voice, sample] += 1
            prev = curr
    
    # TODO memoize the following
    
    def cprob(self, c, k):
        'cprob(c, k) -> Return probability of chord c occurring in key k.'
        return self.cfreq[Func(c, k)]
    
    def nprob(self, n, c, k, v = None):
        'nprob(n, c, k[, v]) -> Return probability of note n occurring in voice v of chord c in key k.'
        return self.nfreq[Tone(n, c), Func(c, k), v] / self.cprob(c, k)
    
    def tprob(self, c1, c, k, vel = None):
        'tprob(c1, c, k[, vel]) -> Return probability of chord c changing to chord c1 in key k under harmonic velocity vel.'
        if c == c1:
            return self.cprob(c, k) # perhaps dependent on vel
        f, f1 = Func(c, k), Func(c1, k)
        return sum(self.tfreq[f1, f, s] / self.cfreq[f, s] for s in self.samples[vel])
    
    def vprob(self, n1, n, c1, c, k, v = None, vel = None):
        '''vprob(n1, n, c1, c, k[, v, vel]) -> 
        Return probability of note n in chord c changing to note n1 in chord c1 
        in key k and voice v under harmonic velocity vel.'''
        if n == n1 and c == c1:
            return self.nprob(n, c, k, v) # perhaps dependent on vel
        f, f1 = Func(c, k), Func(c1, k)
        t, t1 = Tone(n, f), Tone(n1, f1)
        return sum(self.vfreq[t1, t, f1, f, v, s] * self.cfreq[f, s] / (self.nfreq[t, f, v, s] * self.tfreq[f1, f, s]) 
                   for s in self.samples[vel])
