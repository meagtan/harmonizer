import music21

class Freq:
    'Frequency tables'
    def __init__(self):
        self.table = {}
        self.cnt = 0
    def __getitem__(self, item): 
        # TODO include separate samples and sum over None elements of item, including in Func and Tone
        #  In order to do that, perhaps have a nested table forming a tree, where each branch corresponds to a characteristic
        return self.table[item] / self.cnt if self.cnt and item in self.table else 0
    def __setitem__(self, item, value): # TODO include separate samples
        self.cnt += value - self.table[item]
        self.table[item] = value
    
class Env:
    
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
        for curr, prev in zip(cs, cs[1:]):
            self.cfreq[curr] += 1       
            self.tfreq[curr, prev] += 1 
            for voice in voices(curr):
                self.nfreq[note(curr, voice), curr, voice] += 1 # TODO also add sample
                self.vfreq[note(curr, voice), note(pred, voice), curr, pred, voice] += 1
        # TODO this should not count across all samples, but calculate probabilities
        #  based on sums across all samples
    
    # TODO memoize the following
    
    def cprob(self, c, k):
        return self.cfreq[Func(c, k)]
    
    def nprob(self, n, c, k, v = None):
        f = Func(c, k)
        return self.nfreq[Tone(n, c), f, v] / self.cprob(c, k) if self.cprob(c, k) else 0
    
    def tprob(self, c1, c, k, vel):
        f, f1 = Func(c, k), Func(c1, k)
        res = 0
        for s in samples(vel):
            res += self.tfreq[f1, f, s] / self.cfreq[f, s] if self.cfreq[f, s] else 0 
            # TODO encapsulate, perhaps create numeric class and override operators, also including normalization and quotients
        return res # TODO normalize over f1
    
    def vprob(self, n1, n, c1, c, k, v, vel):
        f, f1 = Func(c, k), Func(c1, k)
        t, t1 = Tone(n, f), Tone(n1, f1)
        res = 0
        for s in samples(vel):
            res += self.vfreq[t1, t, f1, f, v, s] * self.cfreq[f, s] / (self.nfreq[t, f, v, s] * self.tfreq[f1, f, s])
        return res
    
    def samples(self, vel):
        pass

class Func:
    def __init__(self, chord, key):
        self.val = (chord.root().diatonicNoteNum - key.tonic.diatonicNoteNum) % 7 + 1
        self.mod = chord.quality, key.mode

class Tone:
    def __init__(self, note, func):
        self.val = (note.diatonicNoteNum - chord.root().diatonicNoteNum) % 7 + 1

class Sample:
    pass