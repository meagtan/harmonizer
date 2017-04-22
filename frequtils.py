from music21 import *
from fractions import Fraction

tones = [n + a for n in 'CDEFGABcdefgab' for a in ['-', '#', '']]
keys = map(key.Key, tones)
chords = [chord.Chord(map(k.pitches.__getitem__, [0, 2, 4])) for k in keys]

class Func(tuple):
    '''
    Stores the diatonic function of a chord in a key, e.g. Func(A7, Dm) represents dominant major in a minor key.
    '''
    def __new__(cls, chord, key):
        try:
            num = (chord.root().diatonicNoteNum - key.tonic.diatonicNoteNum) % 7
            acc = (chord.root().ps - key.pitches[num].ps) % 12
            
            return tuple.__new__(cls, (num, acc, chord.quality, key.mode))
        except AttributeError:
            return ()
    pass

class Tone(tuple):
    '''
    Stores the tone of a note in a key, e.g. Tone(C, DM) returns (7, 0).
    '''
    def __new__(cls, note, key):
        try:
            return tuple.__new__(cls, ((note.diatonicNoteNum - key.tonic.diatonicNoteNum) % 7 + 1,
                                      int(note.alter - key.tonic.alter))) # store accidental
        except AttributeError:
            return ()
    pass

class Sample:
    '''
    A processed sample chorale containing a list of chords, with optionally specified harmonic velocity.
    '''
    def __init__(self, filename):
        self.filename = filename
        self.s = converter.parse(filename)
        self.cs = self.s.chordify()
        ks = self.cs.getKeySignatures()[0]
        
        self.key = key.Key(ks.getScale().tonic, ks.mode)
        self.vel = None # TODO change this, perhaps use qualities other than vel, such as measure ends
        
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
        for c in self.chords():
            yield c.pitches[voice]
    
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

class Prob(Fraction):
    '''
    Integral type with extra normalization factor, to represent probabilities accurately.
    '''
    def __new__(cls, val = 0, norm = None):
        self = Fraction.__new__(cls, val if norm is None else Fraction(val, norm) if norm else 0)
        return self
    
    def __repr__(self):
        return str(self)
    
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
        return Prob(Fraction.__div__(self, other) if other != 0 else 0)
    def __rdiv__(self, other):
        return Prob(other) / self
