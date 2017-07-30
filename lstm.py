# Harmonizing a melody using LSTMs

import torch
import torch.autograd as ag
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from music21 import *
# import key

# key.loaddata()
# logprob, findkey = key.probs()

N, Din, EMBED, HIDDEN, Dout = len(corpus.getBachChorales()), 12, 36, 36, 36

# mat = torch.FloatTensor(Din, Din).fill_(1)

class LSTMHarmonizer(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        nn.Module.__init__(self)
        # self.embed = nn.Embedding(input_dim, embed_dim)
        self.hidden_dim = hidden_dim
        self.lstm = nn.LSTM(input_dim, hidden_dim)
        self.out = nn.Linear(hidden_dim, output_dim)
        self.hidden = self.init_hidden()
    
    def init_hidden(self):
        return (ag.Variable(torch.zeros(1, 1, self.hidden_dim)),
                ag.Variable(torch.zeros(1, 1, self.hidden_dim)))
    
    def forward(self, voice):
        # embeds = self.embed(voice)
        # lstm_out, self.hidden = self.lstm(embeds.view(len(voice), 1, -1), self.hidden)
        lstm_out, self.hidden = self.lstm(voice, self.hidden)
        outs = self.out(lstm_out.view(len(voice), -1))
        return F.log_softmax(outs)

class Sample:
    def __init__(self, filename):
        self.s = converter.parse(filename)
        self.cs = None
        self.nhist = notehist(self.s)
        self.key = self.s.analyze('key') # findkey(self.nhist)
        self.notes = [None] * len(self.s.parts) # may be more complicated for other works
        self.chords = None
        
    # Implement these using __getattr__
    
    # Perhaps store the square root of durations instead of durations, so that
    #  the total duration of note n occurring in chord c can be calculated by N^T C,
    #  where N is the matrix of notes and C the matrix of chords
    # Then the histogram of notes/chords would be the diagonal of N^T N or C^T C,
    #  and classification is done by taking the trace of those matrices multiplied by
    #  different diagonal matrices, or the Frobenius norm of N or C multiplied by the 
    #  square root of those diagonal matrices
    
    # TODO voices have different lengths, break notes wherever another voice changes
    # Or quantize notes based on smallest time interval, which should be universal
    def getnotes(self, voice = None):
        # global mat
        if voice is None:
            return [self.getnotes(v) for v in xrange(len(self.s.parts))]
        if self.notes[voice] is None:
            endtimes = self.s.flat.notesAndRests.stream()._uniqueOffsetsAndEndTimes(endTimesOnly=True)
            self.notes[voice] = [None] * len(endtimes)
            notes = list(self.s.parts[voice].flat.notesAndRests)
            j = 0 # index of current note
            curr = 0.0
            for i in xrange(len(endtimes)):
                self.notes[voice][i] = map(lambda k: (isinstance(notes[j], note.Note) and \
                                           k == pitchtoid(notes[j].pitch, self.key)) * \
                                           (endtimes[i] - curr), range(Din))
                # if current note ends here, go to next note
                if endtimes[i] == notes[j].offset + notes[j].quarterLength:
                    j += 1
                curr = endtimes[i]
            self.notes[voice] = torch.FloatTensor(self.notes[voice])
            n = self.notes[voice].clone().apply_(lambda n: int(n != 0))
            # mat += n[:-1].t().mm(n[1:])
        return self.notes[voice]
    
    def getchords(self):
        if self.chords is None:
            self.cs = self.s.chordify()
            self.chords = []
            for c in self.cs.flat.notesAndRests:
                self.chords.append(
                    map(lambda k: (isinstance(c, chord.Chord) and \
                        k == chordtoid(c, self.key)) * float(c.quarterLength), range(Dout)))
            self.chords = torch.FloatTensor(self.chords)
        return self.chords

# for c in sc.cs.flat.notesAndRests:
#     if isinstance(c, note.Note):
#         c = chord.Chord(c)
#     sc.notes.append(map(lambda n: (isinstance(c, chord.Chord) and \
#                         (n + lstm.pitchtoid(sc.key.tonic)) % 12 in c.normalOrder) * float(c.quarterLength), range(12)))

class SampleIterator(list):
    def __init__(self, files):
        list.__init__(self)
        self.files = files
    
    def __iter__(self):
        for i in xrange(len(self.files)):
            if i == len(self):
                self.append(Sample(self.files[i]))
            yield self[i]

def pitchtoid(p, k = key.Key('C')):
    return (p.pitchClass - k.tonic.pitchClass) % 12 # perhaps include enharmonic information

def chordtoid(c, k = key.Key('C')):
    quals = {'major' : 0, 'minor' : 1, 'diminished' : 2, 'augmented' : 0, 'other' : 0}
    return (c.root().pitchClass - k.tonic.pitchClass) % 12 + 12 * quals[c.quality]

def notehist(s):
    x = torch.FloatTensor(Din).zero_()
    s = s.flat.notes
    
    for n in s:
        l = n.quarterLength
        if n.isChord:
            for m in n.pitchClasses:
                x[m] += l
        else:
            x[n.pitch.pitchClass] += l
    return x

traindata = SampleIterator(corpus.getBachChorales())
model = LSTMHarmonizer(Din, HIDDEN, Dout)
lossfn = nn.KLDivLoss()
optimizer = optim.SGD(model.parameters(), lr = 0.1)

# TODO perhaps instead try training with sums of each voice
def train(eps = 100):
    tot, tot1 = 0.0, None
    for epoch in range(eps):
        i = 0
        s = 0.0
        for sample in traindata:
            chordseq = ag.Variable(sample.getchords().view(-1, 1, 36))
            for notes in sample.getnotes(): # enumerating through each voice
                model.zero_grad()
                model.hidden = model.init_hidden()
                
                # Step 2. Get our inputs ready for the network, that is, turn them into
                # Variables of word indices.
                noteseq = ag.Variable(notes.view(-1, 1, 12))
                
                # Step 3. Run our forward pass.
                tag_scores = model(noteseq)
                
                # Step 4. Compute the loss, gradients, and update the parameters by
                #  calling optimizer.step()
                loss = lossfn(tag_scores, chordseq)
                
                s += loss.data[0]
                loss.backward()
                optimizer.step()
            i += 1
            if i % 15 == 0:
                print epoch, i, s
                tot += s
                s = 0.0
        if tot1 is not None and tot > tot1:
            break
        tot1, tot = tot, 0.0
