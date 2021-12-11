from collections import Counter, defaultdict
import math, re
import kenlm
import operator
import itertools
import copy
import os

model = kenlm.Model('bnc.prune.arpa')

def words(text): return re.findall(r'\w+|[,.?]', text.lower())

WORDS = Counter(words(open('big.txt').read()))

def P(word, N=sum(WORDS.values())): 
    "Probability of `word`."
    return float(WORDS[word] / N)


def known(words): 
    "The subset of `words` that appear in the dictionary of WORDS."
    return set(w for w in words if w in WORDS)


def edits1(word):
    "All edits that are one edit away from `word`."
    letters    = 'abcdefghijklmnopqrstuvwxyz'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    "All edits that are two edits away from `word`."
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))


def suggest(word):
    '''return top 5 words as suggestion, original_word as top1 when original_word is correct'''
    suggest_P = {}
    edits_set = edits1(word).union(set(edits2(word)))
    for candidate in known(edits_set):
        suggest_P[candidate] = P(candidate)
    if word in WORDS:
        suggest_P[word] = 1
    suggest_can = sorted(suggest_P, key=suggest_P.get, reverse=True)[:5]
    
    return suggest_can

###### Task1 ######
def gne_correct_sent_comb(index, sent, wrong_token_index, suggest_word):
    cand_sent_list = []
    if index not in wrong_token_index:
        if index == (len(sent)-1):
            # extend str
            cand_sent_list.extend([copy.deepcopy(sent)])
        else:
            # extend call self
            cand_sent_list.extend(gne_correct_sent_comb(index+1, sent, wrong_token_index, suggest_word))
    else:      
        for word in suggest_word[index]:
            sent[index]=word
            if index == (len(sent)-1):
                cand_sent_list.extend([copy.deepcopy(sent)])
            else:
                cand_sent_list.extend(gne_correct_sent_comb(index+1, sent, wrong_token_index, suggest_word))
    return cand_sent_list

def spelling_check(sentence):    
    sentence = words(sentence)
    wrong_token_index = []
    suggest_word = []
    best_cand = {}

    for i in sentence:
        if i not in WORDS:
            wrong_token_index.append(sentence.index(i))     
    
    for i in sentence:
        suggest_word.append(suggest(i))
    
    cand_sent_list = gne_correct_sent_comb(0, sentence, wrong_token_index, suggest_word)
    blank=' '
    cand_sent=[]
    for i in cand_sent_list:
        cand_sent.append(blank.join(i))

    model = kenlm.Model('bnc.prune.arpa')
    
    for i in cand_sent:
        best_cand[i]=model.score(i, bos = True, eos = True)/len(i)
        sorted_best_cand=sorted(best_cand.items(), key=lambda x: x[1],reverse = True)

    return  sorted_best_cand[0][0], cand_sent
    


print("Task 1 Spelling Check")
task1_input = 'he sold everythin escept the housee'
print("Text:",task1_input,"\n")
print("Candidates:")
task1_result, task1_candidate = spelling_check(task1_input)
for i in task1_candidate[:30]:
    print(i)
print("Number of Candidate:", len(task1_candidate))
print()
print("Result:", task1_result,"\n\n\n")

###### Task2 ######
atcs = {"", "the", "a", "an"}
preps = {"", "about", "at", "by", "for", "from", "in", "of", "on", "to", "with"}
def gne_correct_atc_comb(index, sent, all_index, preps_index, atc_index):
    cand_atc_list = []
    if index not in all_index:
        if index == (len(sent)-1):
            # extend str
            cand_atc_list.extend([copy.deepcopy(sent)])
        else:
            # extend call self
            cand_atc_list.extend(gne_correct_atc_comb(index+1, sent, all_index, preps_index, atc_index))
    else: 
        if index in atc_index:
            for word in atcs:
                sent[index]=word
                if index == (len(sent)-1):
                    cand_atc_list.extend([copy.deepcopy(sent)])
                else:
                    cand_atc_list.extend(gne_correct_atc_comb(index+1, sent, all_index, preps_index, atc_index))
        else:
            for word in preps:
                sent[index]=word
                if index == (len(sent)-1):
                    cand_atc_list.extend([copy.deepcopy(sent)])
                else:
                    cand_atc_list.extend(gne_correct_atc_comb(index+1, sent, all_index, preps_index, atc_index))
    return cand_atc_list

def prep_check(sentence):
    atc_index=[]
    preps_index=[]
    all_index=[]
    cand_atc_list=[]
    best_atc_cand={}
    sentence = words(sentence)
    for i in sentence:
        if i in atcs:
            atc_index.append(sentence.index(i))
            all_index.append(sentence.index(i))
    for i in sentence:
        if i in preps:
            preps_index.append(sentence.index(i)) 
            all_index.append(sentence.index(i))
    cand_atc_list = gne_correct_atc_comb(0, sentence, all_index, preps_index, atc_index)
    blank=' '
    cand_atc_sent=[]
    for i in cand_atc_list:
        a = []
        #i = [x for x in i if x != ""]
        for x in i:
            if x != "":
                a.append(x)
        i = a
        cand_atc_sent.append(blank.join(i))
    model = kenlm.Model('bnc.prune.arpa')
    
    for i in cand_atc_sent:
        best_atc_cand[i] = model.score(i, bos = True, eos = True)/len(i)
        sorted_best_atc = sorted(best_atc_cand.items(), key=lambda x: x[1],reverse = True)

    return  sorted_best_atc[0][0],cand_atc_sent


print("Task 2 Preposition and Article Check")
task2_input = 'look on an picture in the right'
print("Text:",task2_input,"\n")

task2_result, task2_candidate = prep_check(task2_input)
print("Candidates:")
for i in task2_candidate[:30]:
    print(i)
print("Number of Candidate:", len(task2_candidate))
print()
print("Result:", task2_result,"\n\n\n")

 ##### Task3 #####
def process_sent(sent):
    ## TODO ##
    candidate1,_ = spelling_check(sent)
    candidate2,_ = prep_check(candidate1)
    return candidate2
    
    
print("Task 3 Combination")
task3_input = 'we descuss a possible meamin by that'
print("Text:",task3_input,"\n")
comb_result = process_sent(task3_input)
print("Result:", comb_result)

    
