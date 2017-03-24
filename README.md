# harmonizer
Harmonizes a melody with the likeliest sequence of chords using dynamic Bayesian networks.

## Description

A melody is represented as the sequential output of a dynamic Bayesian network, with hidden states for the key and chord sequence on which the melody is played. The program finds the likeliest key and sequence of chords for the melody using the Viterbi algorithm, from the conditional probabilities of chord transitions and voice leading estimated from sample music analyzed using the Python module [music21](https://github.com/cuthbertLab/music21). 

The model of transition probabilities for chords and notes keeps track of two distributions P(c'|c, k) and P(n'|n, c, c', k) for note n moving to note n' along with chord c moving to chord c' in a key k. Using this transition model, it is possible also to detect which enharmonic equivalent of an ambiguous note is more likely to occur based on its neighbors and harmonic context, and thus correct scores in which enharmonics are assigned incorrectly. Moreover, developing a transition model for contrapuntal motion, the program can also find an optimal voice leading for a sequence of chords, optionally accompanied by a melody.

In order to adjust the transition model to variations in samples, we can introduce a parameter λ unique to each sample, which records the general probability that the current chord will change as part of the distribution P(c'|c, k). This parameter can be interpreted as a measure of harmonic velocity. For each chord, we introduce a latent variable z representing a Bernoulli event of changing chords with probability λ, such that z = 0 guarantees the chord will stay the same. Then the transition probability is adjusted as 
```
P(c'|c, k, λ) = P(z = 1|λ) * P(c'|c, k, z = 1) + P(z = 0|λ) * P(c'|c, k, z = 0)
              = λ * P1(c'|c, k) + (1 - λ) * I(c' = c)
```
where I is the indicator function and P1 is the probability distribution to be learned. P1 may take nonzero values even when c' = c, as different chords may have different probabilities of staying the same. The MLE estimate for P1 and the values of λ for each sample may be calculated using the EM algorithm. In order to estimate the chords of a melody using such a model, either λ may be first estimated from only the motion of notes, marginalized with respect to chords, and the chords estimated afterwards using one iteration of the Viterbi algorithm, or λ and the chords may be estimated simultaneously using again the EM algorithm, which would itself use the Viterbi algorithm multiple times to optimize for chords. Though the latter approach would be more accurate, it might be costly to run the Viterbi algorithm multiple times for large melodies, and as melodic motion may differ considerably within and across chords, the former approach would still estimate λ relatively accurately.
