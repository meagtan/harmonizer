from music21     import *
from frequtils   import *
from collections import defaultdict

class Freq:
    'Multiple dimensional frequency table.'
    def __init__(self):
        self.table = {} # should have a None entry keeping count, and other entries frequency tables
        self.table[None] = 0 # perhaps subclass int for this
    
    def __getitem__(self, item): 
        try:
            if item in [None, ()]:
                return self.table[None]
            if not isinstance(item, tuple):
                return self.table[item].table[None]
            if item[0] is True: # normalization
                if len(item) == 1:
                    return 1
                s = 0
                for i in self.table:
                    if i is not None:
                        s += self.table[i][item[2:]]
                return Prob(self.__getitem__(item[1:]), s)
            if item[0] not in [None, ()]:
                return self.table[item[0]][item[1:]]
            return self.table[None]
        except KeyError:
            return 1 # Laplace smoothing
    
    def __setitem__(self, item, value):
        val = self.__getitem__(item)
        if val == 1: # item not in table
            self.table[None] += value + 1 # Laplace smoothing
        else:
            self.table[None] += value - self.__getitem__(item)
        
        if item not in [None, ()]:
            if not isinstance(item, tuple):
                if item not in self.table:
                    self.table[item] = Freq()
                    self.table[item][None] = 1
                self.table[item][None] = value
            elif item[0] not in [None, ()]:
                if item[0] not in self.table:
                    self.table[item[0]] = Freq()
                    self.table[item[0]][None] = 1
                self.table[item[0]][item[1:]] = value
                
    def __iter__(self):
        for i in self.table:
            if i is not None:
                yield i
    def __len__(self):
        return len(self.table) - 1
    
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
        self.kfreq = Freq() # marginal distribution of keys         Key
        self.samples = set()
    
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
        
        vel = sample.vel
        key = sample.key
        self.kfreq[key] += 1
        
        # add sample to samples
        self.samples.add(sample)
        
        prev = None
        for curr in sample.chords():
            f, f1 = Func(curr, key), Func(prev, key)
            self.cfreq[f, sample] += 1     
            self.tfreq[f, f1, sample] += 1 
            for voice, n in enumerate(curr.pitches): # TODO sort pitches first
                try:
                    n1 = prev.pitches[voice] # what if multiple notes are played on the same chord? consider ties
                    t, t1 = Tone(n, key), Tone(n1, key)
                    self.nfreq[t, f, voice, sample] += 1
                    self.vfreq[t, t1, f, f1, voice, sample] += 1
                except:
                    pass
            prev = curr
    
    # TODO memoize the following
    
    def kprob(self, k):
        'kprob(k) -> Return probability of key k.'
        return self.kfreq[True, k]
    
    def cprob(self, c, k):
        'cprob(c, k) -> Return probability of chord c occurring in key k.'
        return self.cfreq[True, Func(c, k)]
    
    def nprob(self, n, c, k, v = None):
        'nprob(n, c, k[, v]) -> Return probability of note n occurring in voice v of chord c in key k.'
        return self.nfreq[True, Tone(n, k), Func(c, k), v] # should normalize over v if not none
    
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

# TODO load table from file, if possible
table = Env()
table.train(corpus.getBachChorales())
