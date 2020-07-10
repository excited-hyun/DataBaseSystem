from konlpy.tag import Mecab
from pymongo import MongoClient
from collections import defaultdict
from bson import ObjectId
from itertools import combinations

stop_word = dict()
DBname = "db20171653"
conn = MongoClient("localhost")
db = conn[DBname]
db.authenticate(DBname, DBname)

def make_stop_word():
    f = open("wordList.txt", "r")
    while True:
        line = f.readline()
        if not line:
            break
        stop_word[line.strip()] = True
    f.close()

def p0() :
    """TO DO: CopyData news to news_freq"""
    col1 = db['news']
    col2 = db['news_freq']
    col2.drop()

    for doc in col1.find():
        contentDic = dict()
        for key in doc.keys():
            if key != "_id":
                contentDic[key] = doc[key]
        col2.insert(contentDic)

def p1() :
    """TO DO: Morph news and update news"""
    for doc in db['news_freq'].find():
        doc['morph'] = morphing(doc['content'])
        db['news_freq'].update({"_id": doc['_id']}, doc)

def morphing(content) :
    mecab = Mecab()
    morphList = []
    for word in mecab.nouns(content):
        if word not in stop_word:
            morphList.append(word)
    return morphList

def p2() :
    """
    TO DO:
    output : news morphs of db.news_freq.findOne()"""
    
    col1 = db['news_freq']
    
    for w in col1.find_one()['morph']:
        print(w)
    

def p3() :
    """
    TO DO:
    copy news morph to new collection named news_wordset"""

    col1 = db['news_freq']
    col2 = db['news_wordset']
    col2.drop()
    for doc in col1.find():
        new_doc = dict()
        new_set = set()
        for w in doc['morph']:
            new_set.add(w)
        new_doc['word_set'] = list(new_set)
        new_doc['news_freq_id'] = doc['_id']
        col2.insert(new_doc)

    
def p4() :
    """
    TO DO:
    output: news wordset og db.news_wordset.findOne()"""

    col1 = db['news_wordset']
    for w in col1.find_one()['word_set']:
        print(w)


class Node:
    def __init__(self,data):
        self.data = data
        self.support = 0
        self.child = []

class Tree:
    def __init__(self, data, children=[]):
        self.data = data
        self.children = list(children)
    def add(self, child):
        self.children.append(child)
    def child(self, data):
        for i  in range(len(self.children)):
            if(data == self.children[i]):
                return self.children[i]

def p5(length) :
    """
    TO DO:
    make frequent item_set
    and insert new collection (candidate_L+"length")
    ex) 1-th frequent item set collection name = candidate_L1"""

    #for doc in db['news_wordset'].find():
        #table = {word : {} for word in doc['word_set']}
    
    L_dict = dict()
    #print(type(table[word]))
    for doc in db['news_wordset'].find():
        for word in doc['word_set']:
            L_dict[word] = [];
    
    index = 0
    N_list = []
    for doc in db['news_wordset'].find():
        insert_list = []
        for word in doc['word_set']:
            #print(1)
            L_list = []
            L_list = L_dict[word]
            L_list.append(index)
            L_dict[word] = L_list
            insert_list.append(word)
        N_list.append(insert_list)
        index += 1
    N_dict = dict()
    for key, value in L_dict.items():
        N_dict[key] = len(L_dict[key])
        L_dict[key] = [L_dict[key], len(L_dict[key])]
        
    #print(N_dict['사실'], N_dict['스마트폰'], N_dict['다양'], N_dict['아이폰'], N_dict['카페'])
    #빈도순으로 정렬
    for i in range(len(N_list)):
        for j in range(len(N_list[i])):
            for k in range(len(N_list[i])-j-1):
                if N_dict[N_list[i][k]] < N_dict[N_list[i][k+1]]:
                    temp = N_list[i][k]
                    N_list[i][k] = N_list[i][k+1]
                    N_list[i][k+1] = temp

    #tree 구현
    Root = Tree("Root")
    node = Root
    R_list = list()
    for i in range(len(N_list)):
        for j in range(len(N_list[i])):
            if j == 0 and N_list[i] not in R_list:
                Root.add(N_list[i])
                R_list.append(N_list[i])

    col = db['candidate_L'+str(length)]
    col.drop()
    min_sup = int((db['news'].count())*0.04)
    L1_dict = dict()
    L1_ID = defaultdict(set)
    for doc in db['news_wordset'].find():
        for word in doc['word_set']:
            L1_dict[word] = 0

    for doc in db['news_wordset'].find():
        for word in doc['word_set']:
            if word in L1_dict:
                L1_dict[word] +=1

    if(length == 1):        #length: 1
        L1_dict = dict()
        L1_ID = defaultdict(set)
        for doc in db['news_wordset'].find():
             for word in doc['word_set']:
                L1_dict[word] = 0

        for doc in db['news_wordset'].find():
            for word in doc['word_set']:
                if word in L1_dict:
                    L1_dict[word] +=1

        for key, value in L1_dict.items():
            if value < min_sup:
                continue
            else:
                L1_set = set()
                L1_doc = {}
                L1_set.add(key)
                #db['candidate_L1'].update({"_id": doc['_id']}, doc)
                L1_doc['item_set'] = list(L1_set)
                L1_doc['support'] = value
                col.insert(L1_doc)
   
    elif(length==2):        #length: 2
        L_addr = defaultdict(set)
        for doc in db['news_wordset'].find():
            for w in doc['word_set']:
                L_addr[w].add(doc['_id'])       #존재하는 기사의 ID모음
        
        node = Root

        L2_set = set()
        for doc in db['candidate_L1'].find():
            for w1 in doc['item_set']:
                for doc1 in db['candidate_L1'].find():   
                    for w2 in doc1['item_set']:
                        if w1 > w2:
                            L2_set.add((w1,w2))

        for Ls in L2_set:
            cnt = 0
            L2_doc = {}
            for w in Ls:
                if cnt == 0:
                    temp =w
                    cnt += 1
                else:
                    if len(L_addr[temp]&L_addr[w]) >= min_sup:
                        #db['candidate_L2'].update({"_id": doc['_id']}, doc)
                        L2_doc["item_set"] = Ls
                        L2_doc['support'] = len(L_addr[temp]&L_addr[w])
                        col.insert(L2_doc)

    elif(length == 3):      #length: 3
        L_addr = defaultdict(set)
        for doc in db['news_wordset'].find():
            for w in doc['word_set']:
                L_addr[w].add(doc['_id'])       #존재하는 기사의 ID모음

        node = Root

        L3_set = set()
        L3_dict = dict()
        L3_dict = L1_dict.copy()
        for key in L1_dict.keys():
            if L1_dict[key] < min_sup:
                del L3_dict[key]
                
        for w1 in L3_dict.keys():
            for w2 in L3_dict.keys():
                for w3 in L3_dict.keys():
                    if w1 != w2 and w1 !=w3 and w2!=w3:
                        if w1> w2 and w2>w3:
                            L3_set.add((w1,w2,w3))
                        elif w1> w3 and w3 >w2:
                            L3_set.add((w1,w3,w2))
                        elif w2> w1 and w1 >w3:
                            L3_set.add((w2,w1,w3))
                        elif w2> w3 and w3 >w1:
                            L3_set.add((w2,w3,w1))
                        elif w3> w1 and w1 >w2:
                            L3_set.add((w3,w1,w2))
                        else:
                            L3_set.add((w3,w2,w1))
        #print("a")
        L3_doc = {}
        for Ls in L3_set:
            #print("b")
            cnt=0
            for w in Ls:
                if cnt == 0:
                    w1 = w
                    cnt += 1
                elif cnt == 1:
                    w2 = w
                    cnt += 1
                else:
                    if len(L_addr[w1]&L_addr[w2]&L_addr[w]) >= min_sup:
                        #db['candidate_L3'].update({"_id": doc['_id']}, doc)
                        L3_doc["item_set"] = Ls
                        L3_doc["support"] = len(L_addr[w1]&L_addr[w2]&L_addr[w])
                        col.insert(L3_doc.copy())    



def p6(length) :
    """
    TO DO:
    make strong association rule
    and print all of string rules
    by length-th frequent item set"""

    min_conf = 0.8

    if(length == 2):
        for doc in db['candidate_L2'].find():
            num = float(doc['support'])     #둘다
            L_list=[]
            for word in doc['item_set']:
                L_list.append(word)
            for doc1 in db['candidate_L1'].find():
                num1 = float(doc1['support'])    #하나
                for word1 in doc1['item_set']:
                    if word1 in L_list and num/num1 >= min_conf:    #0.8보다 큼
                        for w in L_list:
                            if w != word1:
                                result = w
                        print("{} => {:5}{:5}".format(word1,result, num/num1))
                        
    elif(length == 3):
        #단어1, 단어2 => 단어3
        for doc in db['candidate_L3'].find():
            num = float(doc['support'])     #셋다
            L_list=[]
            for word in doc['item_set']:
                L_list.append(word)
            for doc1 in db['candidate_L2'].find():
                num1 = float(doc1['support'])    #둘
                L2_list = list()
                for word1 in doc1['item_set']:
                    L2_list.append(word1)       #두개 -> 한개
                    #print(L2_list)
                if L2_list[0] in L_list and L2_list[1] in L_list and num/num1 >= min_conf:
                    for w in L_list:
                        if w != L2_list[0] and w!= L2_list[1]:
                            result = w
                    print("{}, {} => {:5}{:5}".format(L2_list[0], L2_list[1],result, num/num1))
        
        #단어4=>단어5, 단어6
        for doc in db['candidate_L3'].find():
            num = float(doc['support'])     #셋다
            L_list=[]
            for word in doc['item_set']:
                L_list.append(word)

            for doc1 in db['candidate_L1'].find():
                num1 = float(doc1['support'])    #하나
                for word1 in doc1['item_set']:
                    if word1 in L_list and num/num1 >= min_conf:    #0.8보다 큼
                        R_list=list()
                        for w in L_list:
                            if w == word1:
                                continue
                            R_list.append(w)
                        print("{} => {}, {:5}{:5}".format(word1,R_list[0],R_list[1], num/num1))


def printMenu() :
    print("0. CopyData")
    print("1. Morph")
    print("2. print morphs")
    print("3. print wordset")
    print("4. frequent item set")
    print("5. association rule")


if __name__ == "__main__":
    make_stop_word()
    printMenu()
    selector = int(input())
    if selector == 0:
        p0()

    elif selector == 1:
        p1()
        p3()
    elif selector == 2:
        p2()

    elif selector == 3:
        p4()

    elif selector == 4:
        length = int(input("input length of the frequent item:"))
        p5(length)

    elif selector == 5:
        length = int(input("input length of the frequent item:"))
        p6(length)

