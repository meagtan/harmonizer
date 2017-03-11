### Correcting falsely assigned enharmonics in sheet music

import freqs
from music21 import *

table = freqs.table

class EnharmPitch(pitch.Pitch):
	'Empty subclass to mark enharmonically ambiguous pitches.'
	pass

def correct_enharm(filename): # might add more arguments for control
	'''
	Open and scan through music file, and replace accidentals with likeliest enharmonic equivalents.
	'''
	pass

def likeliest_enharm(n, np, nn, c, cp, cn, k):
	'''
	Estimate the likeliest enharmonic equivalent of the current note based on the previous and next notes, as well as
	the previous, current and next chords.
	'''
	# P(n = e | np, nn, c, cp, cn, k) = Z * P(n = e | np, cp, c, k) * P(nn | n = e, c, cn, k)
	def prob(n, np, cp, c, k):
		'''
		Return probability of current note given previous note, previous chord, current chord and key, 
		conditioning on enharmonic equivalents.
		'''
		# P(n | theta) = P(n = e | theta) + P(n = e1 | theta)
		# P(n | n1, theta) = P(n | n1 = e, theta) * P(n1 = e | theta) + P(n | n1 = e1, theta) * P(n1 = e1 | theta)
		if isinstance(n, EnharmPitch):
			n1 = pitch.Pitch(n)
			return prob(n1, np, cp, c, k) + prob(n.getEnharmonic(), np, cp, c, k)
		if isinstance(np, EnharmPitch):
			n1 = pitch.Pitch(np)
			ne = np.getEnharmonic()
			return prob(n, n1, cp, c, k) * table.nprob(n1, cp, k) + prob(n, ne, cp, c, k) * table.nprob(ne, cp, k)
		return table.vprob(n, np, cp, c, k)
	
	n1 = n.getEnharmonic() # n is a pitch
	if prob(n1, np, cp, c, k) * prob(nn, n1, c, cn, k) > prob(n, np, cp, c, k) * prob(nn, n, c, cn, k):
		return n1
	return n
