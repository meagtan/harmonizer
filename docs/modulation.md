### Key and modulation detection

From the probability models for P(k) and P(n|k) derived from sample corpora of music, we may estimate the key of a piece of music from the histogram of the notes it contains. Assuming, for the intents and purposes of this procedure, that the occurrences of notes in a piece of music are conditionally independent given the key, the probability of a sequence (n<sub>t</sub>)<sub>t</sub> of notes being in key k becomes
```
P(k|(n_t)) = Z P(k) P((n_t)|k) = Z P(k) \prod_t P(n_t|k) = Z P(k) \prod_n P(n|k)^N(n)
```
where Z is a normalization factor independent of k and N(n) is the number of occurrences of note n. Thus, the likeliest key is the key maximizing the log-likelihood
```
log P(k|(n_t)) = log Z + log P(k) + \sum_n N(n) log P(n|k)
```
which is a linear discriminant applied to the histogram of notes. We may thus compare the performance of this classifier with nonparametric linear classifiers such as SVMs and the Krumhansl-Schmuckler algorithm for key detection, whose parameters are hard-coded. 

We may also use this key model to partition a piece of music into several regions with different keys in order to detect modulation. To that end we may model the piece as a sample set of pairs (t, n<sub>t</sub>) of time intervals and notes, generated by a mixture of several distributions, each corresponding to a region with its own key. Regions may be delimited by fitting the time instants to a Gaussian distribution, with variable mean and class weights but common variance, which induces linear decision boundaries and thus connected regions. The likelihood of a note n within a region r is then modelled by the expected value of the likelihood of n occurring in a key k, weighted by the probability of r being in k, or approximately by the likelihood of n being in the key r is most likely to be in. The likelihood of the piece given these model parameters then becomes
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

## Graphical models for segmentation

This may be generalized to a method for the segmentation of sequential data into regions using mixture models. We may think of a sequence (n<sub>t</sub>)<sub>t</sub> (which may be multivalued, as is the case in polyphonic music) as a collection of sample pairs (t, n<sub>t</sub>), and fit this sample dataset, represented as a binary image I<sub>tn</sub>, into a mixture model containing M regions, each restricted to a spatial region and identified with one of K different features, corresponding to keys in the case of modulation. Each region r defines a probability distribution on both t and n<sub>t</sub>, the former based on the spatial locality of r and the latter based on the predominant feature in the region. More formally, if the region indicator Z<sub>tr</sub> takes the value 1 if time t belongs in region r and 0 otherwise, the feature indicator F<sub>rf</sub> 1 if region r belongs in feature f and 0 otherwise, Θ<sub>r</sub> denotes the parameters of the spatial distribution of region r (e.g. mean and variance for Gaussian regions), Ψ<sub>f</sub> the parameters of feature f, π<sub>r</sub> the prior probability of region r and τ<sub>f</sub> the prior probability of feature f, we can use variational Bayesian inference to approximate the joint distribution

```
P(I, Z, F, Θ, Ψ, π, τ) = P(I|Z, F, Θ, Ψ) P(Z|π) P(π) P(Θ) P(F|τ) P(τ) P(Ψ)
```

where

```
P(I|Z, F, Θ, Ψ, π, τ) = \prod_t \prod_n \prod_r P(t,n|Θ_r, F_r, Ψ)^{I_{tn} Z_{tr}}
P(t,n|Θ_r, F_r, Ψ) = P(t|Θ_r) P(n|t, Θ_r, F_r, Ψ)
P(n|t, Θ_r, F_r, Ψ) = \prod_f P(n|t, Θ_r, Ψ_f)^{F_{rf}}
P(Z|π) = \prod_t \prod_r π_r^{Z_{tr}}
P(π) = SymDir(π|M, α)
P(Θ) = \prod_r P(Θ_r)
P(F|τ) = \prod_r \prod_f τ_f^{F_{rf}}
P(τ) = SymDir(τ|K, β)
P(Ψ) = \prod_f P(Ψ_f)
```

Here, the distribution P(n|t, Θ<sub>r</sub>, Ψ<sub>f</sub>) measures the fit of note n occurring at time t to feature f. The dependence on t and Θ<sub>r</sub> reflects the potential anisotropy of the feature, perhaps through an additional variable denoting the starting point of the region. They may be omitted for features such as keys, which simply provide a distribution P(n|k). Likewise, τ and Ψ need not be learned; the features may as well be fixed, as in the case of keys, but may be learned for e.g. motif detection. The distributions P(t|Θ<sub>r</sub>), P(Θ<sub>r</sub>) and P(Ψ<sub>f</sub>) may also be specialized for the given use case, e.g. P(t|Θ<sub>r</sub>) may be a Gaussian, exponential or uniform distribution, P(Θ<sub>r</sub>) an appropriate conjugate prior, and P(Ψ<sub>f</sub>) a product of Dirichlet distributions P(Ψ<sub>f</sub>\[t\]) inducing a categorical distribution P(n|t, Θ<sub>r</sub>, Ψ<sub>f</sub>) = P(n|Ψ<sub>f</sub>\[t-t<sub>r</sub>\]) for the case of theme detection. But for tractable variational inference, it is preferable to keep these distributions in the exponential family.
