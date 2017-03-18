### Inference taking harmonic velocity (the tendency to change chords often) into account

# Harmonic velocity is modelled using a latent Bernoulli process recording whether the current state is stationary or not
# This leads to the following revised probability estimate for chord transitions:
#  p(c'|c, k, vel) = p(z = 1|vel) * p(c'|c, k, z = 1) + p(z = 0|vel) * p(c'|c, k, z = 0)
#                  = vel * p1(c'|c, k) + (1 - vel) * I(c' = c)
# where z is the latent variable, vel its probability of success, p1 the transition probabilities to be learned, and
# I the indicator function.
# The parameters of the distribution p1 and the harmonic velocity vel, assumed to be constant within and variant across
# different samples, can be modelled using the EM algorithm to give the following update rules:
#  vel_m(i)  = 1 - avg(C_m(i, f), f)
#  s_m(i, f) = [(1 - vel_m(i)) * (N(f) - sum(C_m(i, f), i))] / [(1 - vel_m(i)) * N(f) + vel_m(i) * N(f,f) - sum(C_m(i, f), i))]
#  C_(m+1)(i, f) = s_m(i, f) * N_i(f, f)
# where a_m(i, f) is the function a applied to sample i and chord function f in the mth iteration, N(f) the number of instances
# of function f, N(f, f') the number of instances of f transitioning to f', N_i the number of instances of the same in the ith 
# sample, sum(expr, i) the sum of expr across variable i and similarly for avg.
# The probability distribution p1 is calculated after this algorithm as
#  p1(f|f)  = (N(f,f) - sum(C(i, f), i)) / (N(f) - sum(C(i, f), i)),
#  p1(f'|f) = N(f,f') / (N(f) - sum(C(i, f), i)) for f' != f,
# where p1(c'|c, k) = p1(Func(c',k)|Func(c,k)).
