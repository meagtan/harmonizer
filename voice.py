### Generate an optimal voice leading sequence for a sequence of chords

from freqs import *
from music21 import *

class Motion(int):
	'Enumeration type for contrapuntal motion.'
	parallel = 0
	oblique  = 1
	similar  = 2
	contrary = 3
	def __new__(cls, n1, m1, n, m):
		'Motion(n1, m1, n, m) -> the type of motion from tones (n, m) to tones (n1, m1).'
		d = n[0] - n1[0]
		d1 = m[0] - m1[0]
		if d == 0 or d1 == 0:
			return int.__new__(cls, oblique)
		if d == d1:
			return int.__new__(cls, parallel)
		if d * d1 > 0:
			return int.__new__(cls, similar)
		return int.__new__(cls, contrary)

class VoiceEnv(Env):
	'Frequency table storing likelihoods for different types of contrapuntal motion.'
	def __init__(self):
		Env.__init__(self)
		self.mfreq = Freq()	# frequency table for types of motion, taking Motion, current Tones, current Func, Key
	
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
				t = Tone(n, curr)
				self.nfreq[t, f, voice, sample] += 1
				try:
					n1 = prev.pitches[voice] # what if multiple notes are played on the same chord? consider ties
					t1 = Tone(n1, prev)
					self.vfreq[t, t1, f, f1, voice, sample] += 1
					
					# override: update motion frequencies wrt each lower voice
					for v1, m in enumerate(curr.pitches[:voice]):
						m1 = prev.pitches[v1]
						tm, tm1 = Tone(m, curr), Tone(m1, prev)
						self.mfreq[Motion(tn, tm, tn1, tm1), tm, tn, f, sample] += 1	# should there be more conditionals?
				except:
				    pass
			prev = curr
	
	def mprob(self, n1, m1, n, m, c1, c, k):
		'mprob(n1, m1, n, m, c1, c, k) -> The probability of notes (n, m) and chord c moving to (n1, m1) and c1 in key k.'
		f, f1 = Func(c, k), Func(c1, k)
		tn, tn1, tm, tm1 = Tone(n, c), Tone(n1, c1), Tone(m, c), Tone(m1, c1)
		return self.mfreq[True, Motion(tn1, tm1, tn, tm), tm1, tn1, f1]

    
    
    def voiceleading(self, chords, key, melody = None):
    	'Generate voice leading for a sequence of chords, optionally accompanying a melody.'
        # Viterbi algorithm
        probs  = defaultdict(Prob)
        preds  = {}
        length = len(chords)
        
        for ns, p in self.voicings(chord):
            probs[ns, 0] = p
        
        for i in xrange(1, length):
            bestprob = Prob()
            best = None
            for ns, _ in self.voicings(chords[i], k):
                # find max and arg max of transition
                for ns1, _ in self.voicings(chords[i-1], k):
                    newprob = probs[ns1, i - 1] * self.voicingprob(ns, chords[i], k, ns1, chords[i-1])
                    if probs[ns, i] < newprob:
                        probs[ns, i] = newprob
                        preds[ns, i] = ns1
                # update bestprob and bestchor
                if bestprob < probs[ns, i]:
                    bestprob = probs[ns, i]
                    best = ns
        
        # construct voice leading
        ns = best
        voices = [ns]
        for i in xrange(length - 1, 0, -1):
            ns = preds[ns, i]
            voices.append(ns)
        voices.reverse()
        
        return voices, bestprob

    def voicings(self, chord, key, prev = None):
    	'Generate voicings of a chord, optionally coming after another chord, along with their probabilities.'
    	pass
    
    def voicingprob(self, ns, c, k, ns1 = None, c1 = None):
        'Return the probability of a voicing of a chord in a given key, optionally after another chord.'
        pass
