## Recognizing modulation using EM
# The goal is to separate a piece of music into k regions such that each region is in a different key.
# P(r|(n_t)) ~ P(r) P(t|r) sum(P(k|r) P(n_t|t, k), k) ≈ P(r) P(t|r) P(n_t|t, k_max)
# P(t|r) is approximated as a normal distribution with variable mean but common variance.
# The region boundaries are controlled by the region means and weights, which provides cleaner and wider decision boundaries.
# The most likely key within a region is optimized by looking at the histogram of the region.

from histogram import *

def modulation(table, s, n):
    '''
    Identify modulation in a sample s by dividing it into at most n regions.
    '''
    w = {} # w[t, r] corresponds to the weight of time t for region r
    c = [1] * n # c[r] corresponds to the class weight of region r
    m = [1] * n # m[r] corresponds to the class mean of region r
    k = [1] * n # k[r] corresponds to the most likely key for region r
    v = 1  # v is the common class variance, initially irrelevant and set to 1
    ms = list(m.notes for m in s.cs if isinstance(m, stream.Measure) # list of measures, simplify late
    l = len(ms) # total duration of sample
    km = findkey(table, s) # key of whole piece
    
    # initially, divide sample evenly
    for r in xrange(n):
        m[r] = (r + 0.5) * l / n
    
    # loop until convergence
    for _ in xrange(10): # TODO better condition, such as regions not changing
        # find b[r] from c[r] and m[r]
        b = boundaries(c, m, v, l)
        for r in b:
            # calculate k[r] from b[r]
            k[r] = findkey(table, reduce(concat, ms[b[r][0]:b[r][1]])) # or perhaps compute k[r] from matrix product of s and w
        # calculate weights
        for t in xrange(l):
            rs = dict((r, exp(-(t-m[r]) ** 2 / v + log(c[r]) + loglikelihood(table, ms[t], k[r]))) for r in b)
            rm = max(rs, lambda r: rs[r])
            # rsum = sum(rs[r] for r in rs)
            for r in b:
                w[t, r] = float(r == rm) # approximation for rs[r] / rsum
        # update parameters
        for r in b:
            c[r] = sum(w[t,r] for t, r1 in w if r == r1) / sum(w[t,r1] for t, r1 in w if r in b)
            m[r] = sum(t * w[t,r] for t, r1 in w if r == r1) / sum(w[t,r] for t, r1 in w if r == r1)
        v = sum((t - m[r1]) ** 2 * w[t,r1] for t, r1 in w if r1 in b) / sum(w[t,r1] for t, r1 in w if r1 in b)
    return boundaries(c, m, v, l)

def boundaries(c, m, s, l):
    'Calculate region boundaries from region means and weights.'
    def discr(t, r):
        'Linear discriminant for classifying a time instant to a region.'
        return 2 * m[r] * t - m[r] ** 2 + s ** 2 * log(c[r])
    def intersect(r, r1):
        'The time the discriminants of two different regions intersect.'
        # 2(m[r]-m[r1])t - m[r]^2 + m[r1]^2 + s^2 log(c[r]/c[r1]) = 0
        return (m[r] + m[r1]) / 2 - s ** 2 * log(c[r]/c[r1]) / (2 * (m[r] - m[r1]))
    b = {}
    t = 0
    n = len(c)
    
    # find most likely region in the beginning, hopefully region 0
    r = max(xrange(n), key = lambda r: discr(t, r))
    while t < l:
        # find the region first to overcome the discriminant of the current region and set it to the next region
        # perhaps optimize this through dynamic programming
        try:
            t1, r1 = min(((intersect(r, r1), r1) for r1 in xrange(n) if r != r1 and intersect(r, r1) > t))
        except ValueError: # empty iterator
            t1, r1 = l, r
        b[r] = t, t1
        r, t = r1, t1
    return b
