from fractions import Fraction

class Func(tuple):
    '''
    Stores the diatonic function of a chord in a key, e.g. Func(A7, Dm) represents dominant major in a minor key.
    '''
    def __new__(cls, chord, key):
        return tuple.__new__(cls, ((chord.root().diatonicNoteNum - key.tonic.diatonicNoteNum) % 7 + 1,
                                   chord.quality, key.mode))
    pass

class Tone(int):
    '''
    Stores the tone of a note in a chord, e.g. Tone(C, DM) returns 7.
    '''
    def __new__(cls, note, func):
        return int.__new__(cls, (note.diatonicNoteNum - chord.root().diatonicNoteNum) % 7 + 1)
    pass

class Sample:
    '''
    A processed sample chorale containing a list of chords, with optionally specified harmonic velocity.
    '''
    def __init__(self, filename):
        self.filename = filename
        self.cs = corpus.parse(filename).chordify()
        ks = cs.getKeySignatures()[0]
        
        self.key = key.Key(ks.getScale().tonic, ks.mode)
        self.vel = None # TODO change this, perhaps use qualities other than vel, such as measure ends
    
    def chords(self):
        'Iterates through each chord of sample.'
        for m in self.cs:
            # parse each chord as a list of notes, keeping ties in mind
            if isinstance(m, stream.Measure):
                for c in m.notes(): # cannot call notes directly apparently
                    yield c
    
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
