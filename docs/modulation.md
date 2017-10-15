### Key and modulation detection

From the probability models for P(k) and P(n|k) derived from sample corpora of music, we may estimate the key of a piece of music from the histogram of the notes it contains. Assuming, for the intents and purposes of this procedure, that the occurrences of notes in a piece of music are conditionally independent given the key, the probability of a sequence (n_t) of notes being in key k becomes
```
P(k|(n_t)) = Z P(k) P((n_t)|k) = Z P(k) \prod_t P(n_t|k) = Z P(k) \prod_n P(n|k)^N(n)
```
where Z is a normalization factor independent of k and N(n) is the number of occurrences of note n. Thus, the likeliest key is the key maximizing the log-likelihood
```
log P(k|(n_t)) = log Z + log P(k) + \sum_n N(n) log P(n|k)
```
which is a linear discriminant applied to the histogram of notes. We may thus compare the performance of this classifier with nonparametric linear classifiers such as SVMs and the Krumhansl-Schmuckler algorithm for key detection, whose parameters are hard-coded. 

We may also use this key model to partition a piece of music into several regions with different keys in order to detect modulation. To that end we may model the piece as a sample set of pairs (t, n) of time intervals and notes, generated by a mixture of several distributions, each corresponding to a region with its own key. Regions may be delimited by fitting the time instants to a Gaussian distribution, with variable mean and class weights but common variance, which induces linear decision boundaries and thus connected regions. The likelihood of a note n within a region r is then modelled by the expected value of the likelihood of n occurring in a key k, weighted by the probability of r being in k, or approximately by the likelihood of n being in the key r is most likely to be in. The likelihood of the piece given these model parameters then becomes
```
P((n_t)|Θ) = \prod_t P(n_t|Θ) = \prod_t (\sum_r P(r|Θ) P(n_t|r,Θ)) = \prod_t (\sum_r P(r|Θ) P(t|r,Θ) P(n_t|k(r)))
```
where k(r) is the MAP estimate of the key for region r and Θ is the set of model parameters. This likelihood can then be maximized for the model parameters using the EM algorithm, as implemented [here](modulation.py).

Below is a demonstration of how the EM algorithm works to iteratively optimize decision boundaries for regions, for two pieces of music with very different frequencies of modulation: Bach's *Chaconne in D minor*, and Beethoven's *Grosse Fuge in B-flat major*. The weighted normal distributions plotted in black depict the probability distributions of each region, whose boundaries are delimited by the intersections between each consecutive distribution, plotted in relation to measure number. Different colors represent different keys. The algorithm continues iterating until the likelihood decreases or stays the same, due to approximations or decreasing variance, and returns the segmentation with the greatest likelihood.

<table style="border:none;">
  <tr>
    <td width="50%" align="center" valign="top">
      <img src="https://gist.github.com/meagtan/019fda9f8643174450cf218d926373b9/raw/6b0f260613e701342d0ef97ebfd9808fa7e3bf4a/chac7.gif" width="100%"/>
      <p align="center">Chaconne<br /> Red = D minor, green = D major</p>
    </td>
    <td width="50%" align="center" valign="top">
      <img src="https://gist.github.com/meagtan/019fda9f8643174450cf218d926373b9/raw/6b0f260613e701342d0ef97ebfd9808fa7e3bf4a/fug20.gif" width="100%"/>
      <p align="center">Grosse Fuge<br /> Blue = G major, green = F major, red = B-flat major, cyan = G-flat major, magenta = F minor, yellow = C minor, black = A-flat major</p>
    </td>
  </tr>
</table>