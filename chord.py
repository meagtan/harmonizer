import music21
import heapq as hp

def inferchords(notes, key = None, voice = None, vel = None): # TODO generalize as kwargs
    '''
    inferchords(notes, key = None, voice = None, vel = None)
    Returns the most probable sequence of chords for the given sequence of notes, with optional information
    given for the key, voice, signature and harmonic rhythm.
    The key is inferred if not provided; the other variables are averaged or not considered.
    '''
    
    # Dijkstra's algorithm, modified to change (min,+) into (max,*) for distances
    openset = []
    probs   = {}
    preds   = {}
    length  = len(notes)
    
    for c in chords(notes[0]):
        for k in [key] if key else keys:
            probs[0, c, k] = cprob(c, k) * nprob(notes[0], c, k, voice)
            hp.heappush(openset, (-probs[0, c, k], (0, c, k))) # negative for max heap
    
    while openset:
        i, c, k = hp.heappop(openset)[1]
        
        # found likeliest complete sequence
        if i == length - 1: 
            res = []
            while (i, c, k) in preds:
                res.append(c)
                i, c, k = preds[i, c, k]
            res.append(c)
            res.reverse()
            return k, res 
        
        for c1 in chords(notes[i+1]):
            newprob = probs[i, c, k] * cprob(c1, k, c, vel) * nprob(notes[i+1], c, k, voice, notes[i], vel)
            newitem = (i + 1, c1, k)
            if newitem not in probs or newprob > probs[newitem]:
                probs[newitem] = newprob
                preds[newitem] = i, c, k
                hp.heappush(openset, (newprob, newitem))
    return None