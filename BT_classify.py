import BTkey
from pymongo import MongoClient
from nltk import word_tokenize
from nltk.corpus import stopwords
import numpy as np
from sklearn import svm
from collections import Counter, defaultdict

# This object will hold the training data
class GawkerTrainer(object):
    
    def __init__(self, c, f):
        self.group = c
        self.features = f

# Call out common words that are unlikely to hold meaning for the model.
stopwords = stopwords.words('english')
gawk_class = ['gadgets & technology', 'science & science fiction', "celebrity, sex & womens fashion", 'productivity tips', 'sports', 'news, futuristic ideas & technology', 'Silicon Valley gossip']

print "Work, work, work!"
print "Retrieving data from the database..."
client = MongoClient(BTkey.mongoLab())
db = client['busquetweet-db']
gawk = db.gwker

# add the following words to the list of stopwords:
# still, also, year, state, first, like, sure, might
for w in ['still', 'also', 'year', 'would', 'could', 'state', 'first', 'like', 'sure', 'might']:
    stopwords.append(w) 

# Tokenize the provided Twitter data and produce a list of binary values for X
def c_choose(c):
    username = []
    usernames = []
    MXs = []
    tweets = db.tweeps
    data2 = tweets.find({},{'TweetContent.Text':1, '_id': 1, 'Hashtags': 1, 'AssocTweets': 1, 'UserName': 1})
    
    # Go through each entry in BTdb
    for d in data2:
        t = ""
        htt = ""
        att = ""
        try:
            txt = d['TweetContent']['Text']
            for s in txt:
                t += s + " "
            hts = d['Hashtags'].keys()
            for ht in hts:
                htt +=  ht + " "
        except:
            pass
        try:
            ats = d['AssocTweets'][0]
            for at in ats:
                att += at + " "
        except:
            pass
        usernames.append(d['UserName'])
        t += htt
        t += att
        t = t.lower()
        t_tokens = word_tokenize(t)
        x = []
        feats = c.features
        for feat in feats:
            if feat in t_tokens:
                x.append(1)
            else: 
                x.append(0)
        #x = np.matrix(x)
        MXs.append(x)
    return MXs, usernames

# structure the training set
def structure_train():
    # Create a dictionary containing dependent and independent variables for the models.
    dset = {}
    print "Classes:"
    # Each model will classify one dependent variable. 
    for c in [giz, io9, jez, hac, dspin, splo, valley]:
        X = []
        y = []
        data = gawk.find().sort([['_id', -1]])
        for article in data:
            x = []
            y.append(article['class'])
            t_tokens = word_tokenize(article['text'].lower())
            feats = c.features
            for feat in feats:
                if feat in t_tokens:
                    x.append(1)
                else: 
                    x.append(0)
            X.append(x)
        print "%s, %d features" % (c.group, len(c.features))
        dset[c.group] = [np.matrix(X), np.matrix(y)]
    print "----------------------------------------"
    return dset

# Gather the top features for each class
for i, c in enumerate(gawk_class):
    data = gawk.find({'class': c})
    text = ''
    top_words = []        

    wordbank = Counter()
    for item in data:
        text = (item['text'])
        token = word_tokenize(text)
        
        words = [w for w in token if w not in stopwords]
        words = [w for w in words if len(w) > 3]
        for word in words:
            wordbank[word] += 1

    w_count = sorted(wordbank.values(), reverse=True)
    
    for n in w_count:
        if len(set(top_words)) > 40:
            break
        for k in wordbank.keys():
            if wordbank[k] == n:
                top_words.append(k)
        
            top_words = list(set(top_words))
        
        # Create an object for training data gathered at each of the Gawker sites that 
        if i == 0:
            giz = GawkerTrainer(c, top_words)
        elif i == 1:
            io9 = GawkerTrainer(c, top_words)
        elif i == 2:
            jez = GawkerTrainer(c, top_words)
        elif i == 3:
            hac = GawkerTrainer(c, top_words)
        elif i == 4:
            dspin = GawkerTrainer(c, top_words)
        elif i == 5:
            splo = GawkerTrainer(c, top_words)
        elif i == 6:
            valley = GawkerTrainer(c, top_words)
            
print "Classifying the Twitter data...\n"

all_classes = [giz, io9, jez, hac, dspin, splo, valley]
dset = structure_train()

# This dictionary will retain the identified classes for each evaluated Twitter user. 
classified_tweeps = defaultdict(list)

for c in all_classes:
    temp_y = []
    MXs, usernames = c_choose(c)
    for kind in dset[c.group][1].tolist()[0]:
        if kind == c.group:
            temp_y.append(kind)
        else:
            temp_y.append('other')
    temp_y = np.matrix(temp_y)
    Xtrain = dset[c.group][0]
    ytrain = np.ravel(temp_y)
    SVMtrain = svm.SVC(kernel='linear', gamma=2)
    SVMtrain.fit(Xtrain, ytrain)
    for i, Xtweet in enumerate(MXs):
        prediction = SVMtrain.predict(Xtweet)[0]
        if prediction == c.group:
            classified_tweeps[usernames[i]].append(prediction)

for name in usernames:
    if name not in classified_tweeps.keys():
        classified_tweeps[name].append("Awww, man! This user does not appear to have much interest in the Gawker media powering this classifier. They either do not engage in the right conversations OR they don't talk enough to determine interest.")

# Finally, report the findings after putting in work!
for u in classified_tweeps.keys():
    print "\n"
    print "Twitter User: %s" % (u)
    for classificado in classified_tweeps[u]:
        print classificado
    print "-------------------------------"