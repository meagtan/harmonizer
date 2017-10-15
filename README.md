# harmonizer
Harmonizes a melody with the likeliest sequence of chords using dynamic Bayesian networks.

## Description

A melody is represented as the sequential output of a dynamic Bayesian network, with hidden states for the key and chord sequence on which the melody is played. The program finds the likeliest key and sequence of chords for the melody using the Viterbi algorithm, from the conditional probabilities of chord transitions and voice leading estimated from sample music analyzed using the Python module [music21](https://github.com/cuthbertLab/music21). 

The model of transition probabilities for chords and notes keeps track of two distributions P(c'|c, k) and P(n'|n, c, c', k) for note n moving to note n' along with chord c moving to chord c' in a key k. Using this transition model, it is possible also to detect which enharmonic equivalent of an ambiguous note is more likely to occur based on its neighbors and harmonic context, and thus correct scores in which enharmonics are assigned incorrectly. Moreover, developing a transition model for contrapuntal motion, the program can also find an optimal voice leading for a sequence of chords, optionally accompanied by a melody.
