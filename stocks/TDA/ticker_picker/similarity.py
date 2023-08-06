# Program to measure the similarity between
# two sentences using cosine similarity.
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
#from spicy_test import spicy_test
#from spicy import spicy

def similarity(X: str,Y: str) -> int:
    # tokenization
    X_set = set(word_tokenize(X))
    Y_set = set(word_tokenize(Y))

    # sw contains the list of stopwords
    #sw = stopwords.words('english')
    l1 =[];l2 =[]

    # form a set containing keywords of both strings
    rvector = X_set.union(Y_set)
    for w in rvector:
        if w in X_set: 
            l1.append(1) # create a vector
        else: 
            l1.append(0)
        if w in Y_set: 
            l2.append(1)
        else: 
            l2.append(0)
    c = 0

    # cosine formula
    for i in range(len(rvector)):
        c+= l1[i]*l2[i]
    cosine = (c / float((sum(l1)*sum(l2))**0.5))
    return(cosine)                       
