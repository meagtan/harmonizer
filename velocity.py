### Inference taking harmonic velocity (the tendency to change chords often) into account

# Harmonic velocity is modelled using a latent Bernoulli process recording whether the current state is stationary or not
# This leads to the following revised probability estimate for chord transitions:
#  p(c'|c, k, vel) = p(z = 1|vel) * p(c'|c, k, z = 1) + p(z = 0|vel) * p(c'|c, k, z = 0)
#                  = vel * p1(c'|c, k) + (1 - vel) * I(c' = c)
# where z is the latent variable, vel its probability of success, p1 the transition probabilities to be learned, and
# I the indicator function.
# The parameters of the distribution p1 and the harmonic velocity vel, assumed to be constant within and variant across
# different samples, can be modelled using the EM algorithm to give the following update rules:
#  vel_m(i)  = 1 - sum(C_m(i, f), f) / T_i
#  w_m(i, f) = [(1 - vel_m(i)) * (N(f) - sum(C_m(i, f), i))] / [(1 - vel_m(i)) * N(f) + vel_m(i) * N(f,f) - sum(C_m(i, f), i))]
#  C_(m+1)(i, f) = w_m(i, f) * N_i(f, f)
# where a_m(i, f) is the function a applied to sample i and chord function f in the mth iteration, N(f) the number of instances
# of function f, N(f, f') the number of instances of f transitioning to f', N_i the number of instances of the same in the ith 
# sample, sum(expr, i) the sum of expr across variable i and T_i is the length of sample i.
# The probability distribution p1 is calculated after this algorithm as
#  p1(f|f)  = (N(f,f) - sum(C(i, f), i)) / (N(f) - sum(C(i, f), i)),
#  p1(f'|f) = N(f,f') / (N(f) - sum(C(i, f), i)) for f' != f,
# where p1(c'|c, k) = p1(Func(c',k)|Func(c,k)).

from freqs import *

class VelEnv(Env):
    '''
    Program environment containing probabilities for each chord, note and transition, acquired from sample chord sequences,
    keeping harmonic velocity in mind.
    '''
    
    def __init__(self):
        Env.__init__(self)
        self.c = defaultdict(lambda: None) # stores c[s, f]
    
    def train(self, filenames):
        'Train probabilities from given iterator of filenames, inferring their harmonic velocities.'
        for f in filenames:
            s = Sample(f)
            if s not in self.samples:
                print 'Processing %s...' % f
                self.process(s)
        
        # run EM algorithm on samples
        # initialize c
        for s in self.samples:
            for f in self.tfreq:
                self.c[s, f] = float(self.tfreq[f, f, s]) / 2   # 1/2 picked as starting value for all w
        # loop until convergence
        for _ in xrange(10): # TODO find better loop condition
            # calculate velocity for each sample
            for s in self.samples:
                s.vel = 1 - sum(self.c[s, f] for f in self.tfreq) / sum(self.tfreq[f, f, s] for f in self.tfreq)
            # calculate w and c for each sample and function
            for s in self.samples:
                for f in self.tfreq:
                    n1 = sum(self.c[s1, f] for s1 in self.samples)
                    n2 = self.tfreq[f, f] - n1
                    n1 = self.cfreq[f] - n2
                    self.c[s, f] = (1 - s.vel) * n1 / ((1 - s.vel) * n1 + s.vel * n2) * self.tfreq[f, f, s]
        # subtract c from each probability of f -> f
        # perhaps move this into tprob
        for s in self.samples:
            for f in self.tfreq:
                self.tfreq[f, f, s] -= self.c[s, f]
    
    def tprob(self, c1, c, k, vel = None):
        'tprob(c1, c, k[, vel]) -> Return probability of chord c changing to chord c1 in key k under harmonic velocity vel.'
        p = Env.tprob(self, c1, c, k)
        if vel is not None:
            p *= vel
            if c1 == c:
                p += 1 - vel
        return p
