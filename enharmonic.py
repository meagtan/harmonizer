### Correcting falsely assigned enharmonics in sheet music

import freqs
from music21 import *

table = freqs.table

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
	n1 = enharm_eqv(n)
	# problem: what if np, nn are also ambiguous? condition across enharmonics, in a function replacing tprob
	if table.tprob(n1, np, cp, c, k) * table.tprob(nn, n1, c, cn, k) >
	   table.tprob( n, np, cp, c, k) * table.tprob(nn,  n, c, cn, k):
		return n1
	return n
