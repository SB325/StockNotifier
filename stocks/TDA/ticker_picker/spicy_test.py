import numpy as np

# for each headline, a score will be generated based on it's spicy score
def spicy_test(headline: str, spicy: dict, verbose: bool):
    #headline = "How the west was won ho"
    #headlinelist = headline.split(' ')
    #spicy={'howdy':1,'west':3,'ho':4}
    
    test = []
    match = []
    headline_mod=headline
    for sp in spicy.keys():
        if sp.lower() in headline.lower():
            test.append(spicy[sp])
            match.append(sp)
            loc = headline_mod.lower().find(sp.lower())
            score_string = str(spicy[sp])
            score_length = len(score_string)
            while loc>=0:
                headline_mod=headline_mod[:loc+len(sp)] + \
                    '(' + score_string + ')' + \
                    headline_mod[loc+len(sp):]
                loc = headline_mod.lower().find(sp.lower(),loc+len(sp)+score_length+2)
            
    score = np.prod(test)
    if any(np.array(test)<0):
        score = -abs(score)

    if verbose:
        print(f"Test val: {test}")
        print(f"Test value product: {score}")
        print(f"Spicy words found: {match}")

    spices = {'score':score,'words':match, 'modified_headline':headline_mod}
    return spices
