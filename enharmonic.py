### Correcting falsely assigned enharmonics in sheet music

import freqs
from music21 import *
import itertools

table = freqs.table

class EnharmPitch(pitch.Pitch):
	'Empty subclass to mark enharmonically ambiguous pitches.'
	def __new__(cls, p):
		return pitch.Pitch.__new__(cls, p)
	pass

def correct_enharm(filename): # might add more arguments for control
	'''
	Open and scan through music file, and replace accidentals with likeliest enharmonic equivalents.
	'''
	s = converter.parse(filename) # pass args and kwargs here if necessary
	# look for enharmonically ambiguous notes and mark them
	for n in s.flat.notes:
		if enharm_ambiguous(n.pitch): # TODO more arguments for key, histogram, etc.
			n.pitch = EnharmPitch(n.pitch)
	# replace enharmonically ambiguous notes with their likeliest equivalents
	for p in s.parts:
		np = None
		for i, n in enumerate(p.flat.notes):
			if isinstance(n.pitch, EnharmPitch):
				n.pitch = likeliest_enharm(n.pitch, np, p.flat.notes[i+1] if len(p.flat.notes) > i+1 else None,
										   c, cp, cn, k) # TODO find c, cp, cn, k
			np = n
	pass

def likeliest_enharm(n, np, nn, c, cp, cn, k):
	'''
	Estimate the likeliest enharmonic equivalent of the current note based on the previous and next notes, as well as
	the previous, current and next chords.
	'''
	# P(n = e | np, nn, c, cp, cn, k) = Z * P(n = e | np, cp, c, k) * P(nn | n = e, c, cn, k)
	def prob(n, np, cp, c, k): # TODO np, cp can be None
		'''
		Return probability of current note given previous note, previous chord, current chord and key, 
		conditioning on enharmonic equivalents.
		'''
		# P(n | theta) = P(n = e | theta) + P(n = e1 | theta)
		# P(n | n1, theta) = P(n | n1 = e, theta) * P(n1 = e | theta) + P(n | n1 = e1, theta) * P(n1 = e1 | theta)
		if n is None:
			return freqs.Prob(1, 2)
		if np is None:
			if isinstance(n, EnharmPitch):
				return table.nprob(n, c, k) + table.nprob(n.getEnharmonic(), c, k)
			return table.nprob(n, c, k)
		if isinstance(n, EnharmPitch):
			n1 = pitch.Pitch(n)
			return prob(n1, np, cp, c, k) + prob(n.getEnharmonic(), np, cp, c, k)
		if isinstance(np, EnharmPitch):
			n1 = pitch.Pitch(np)
			ne = np.getEnharmonic()
			return prob(n, n1, cp, c, k) * table.nprob(n1, cp, k) + prob(n, ne, cp, c, k) * table.nprob(ne, cp, k)
		return table.vprob(n, np, cp, c, k)
	n = pitch.Pitch(n)
	n1 = n.getEnharmonic() # n is a pitch
	if prob(n1, np, cp, c, k) * prob(nn, n1, c, cn, k) > prob(n, np, cp, c, k) * prob(nn, n, c, cn, k):
		return n1
	return n

def enharm_ambiguous(p, *args):
	'Return True if it is uncertain whether p or its enharmonic equivalent should be in its place.'
	pass
