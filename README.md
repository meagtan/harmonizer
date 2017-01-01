# harmonizer
Inferring sequences of chords from melodies using dynamic Bayesian networks

## Description

A melody is represented as the sequential output of a dynamic Bayesian network, with hidden states for the key and chord sequence on which the melody is played. The program finds the likeliest key and sequence of chords for the melody using Viterbi's algorithm, from the conditional probabilities of chord transitions and voice leading estimated from sample music analyzed using the Python module [music21](https://github.com/cuthbertLab/music21).
