from tweepy import API, OAuthHandler, Cursor
from tweepy.streaming import StreamListener
import BTkey
import collections
import operator
import pymongo

class Tweep(object):

    # Tweep will gather relevant user data when fed a user name or an id
    def __init__(self, user_name):
        u_data = api.get_user(user_name)
        self.user_name = u_data._json["screen_name"]
        self.u_id = u_data._json["id"]
        self.description = u_data._json["description"]

    # Collect id for replies and mentions in the user's timeline.
    def converse(self):
        self.tl = api.user_timeline(id=self.u_id) # add count=n to increase the number of statuses collected
        mdict = collections.Counter()
        rdict = collections.Counter()
        hdict = collections.Counter()

        for status in self.tl:
            rdict[status._json["in_reply_to_user_id"]] += 1

            for mention in status._json["entities"]["user_mentions"]:
                mdict[mention["id"]] += 1
                
            for ht in status._json["entities"]["hashtags"]:
                try:
                    hdict[ht['text']] += 1
                except:
                    pass
        # Remove any None values from the Counter objects if they exist. 
        for d in [mdict, rdict, hdict]:
            if None in d:
                del d[None]
            
        self.replies = rdict
        self.hashtags = hdict
        self.mentions = mdict
        
    # Collect the text content and urls from the statuses in the timeline.
    def tcontent(self):
        links = []
        tw_text = []
        for status in self.tl:
            tw_text.append(status.text)
            for link in status._json['entities']['urls']:
                try:
                    links.append(link["url"])
                except:
                    pass
        self.tw_text = tw_text
        self.links = links
    
    # Collect the text content of statuses returned from a search query.
    # hasht is a tuple consisting of a string (hashtag) and an integer (hashtag's frequency in the target tweep's timeline). 
    def associations(self, hasht):
        hashtag = "#{0}".format(hasht[0])
        # The search query will return more statuses for more common hashtags
        search = api.search(hashtag, rpp=10*hasht[1])
        assoc = []
        try:
            for status in search:
                assoc.append(status.text)
        except:
            pass
        self.assoc = {hasht[0]: assoc}
        
    # Accepts the dictionary of hashtags and returns a list of up to 10 of the most common
    def top_hashtags(self):
        if len(self.hashtags) > 10:
            self.tht = sorted(self.hashtags.items(), key=operator.itemgetter(1), reverse=True)[:10]
        else:
            self.tht = sorted(self.hashtags.items(), key=operator.itemgetter(1), reverse=True)
            
    # Accepts the dictionary of replies and returns a list of up to 10 of the most common
    def top_replies(self):
        if len(self.replies) > 5:
            self.tr = sorted(self.replies.items(), key=operator.itemgetter(1), reverse=True)[:5]
        else:
            self.tr = sorted(self.replies.items(), key=operator.itemgetter(1), reverse=True)
            
    # Accepts the dictionary of mentions and returns a list of up to 10 of the most common
    def top_mentions(self):
        if len(self.mentions) > 5:
            self.tm = sorted(self.mentions.items(), key=operator.itemgetter(1), reverse=True)[:5]
        else:
            self.tm = sorted(self.mentions.items(), key=operator.itemgetter(1), reverse=True)

    # Collect text content of tweets from the list of top replies and mentions.
    def context_tweets(self):
        r_text = []
        try:
            for reply in self.tr:
                for status in api.user_timeline(reply[0]):
                    r_text.append(status.text)
        except:
            pass
        try:
            for mention in self.tm:
                for status in api.user_timeline(mention[0]):
                    r_text.append(status.text)
        except:
            pass

        self.socialtext = r_text        

    # Converts dictionary keys into strings for DB entry. 
    def d_convert(self, d):
        d2 = dict()
        for k, v in d.iteritems():
            d2[str(k)] = v
        return d2        
        
    # Insert the collected twitter data into the database, BTdb.  
    def mongo_filler(self):
        client = pymongo.MongoClient()
        db = client.BTdb
        tweeps = db.tweeps
        tweeps.update({'_id': self.u_id}, {'UserName': self.user_name,
                       'Description': self.description,
                       'TweetContent': {'Text': self.tw_text, 'Links': self.links},
                       'Replies': self.d_convert(self.replies),
                       'Mentions': self.d_convert(self.mentions),
                       'Hashtags': self.hashtags}, upsert=True)

        for ht in self.tht:
            self.associations(ht)
            tweeps.update({'_id': self.u_id}, {"$push": self.assoc})

        tweeps.update({'_id': self.u_id}, {"$push": {'AssocTweets': self.socialtext}})

# preparing oauth
ckey = BTkey.keychain('api_key')
csecret = BTkey.keychain('api_secret')
atoken = BTkey.keychain('access_token')
asecret = BTkey.keychain('token_secret')

auth = OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)

# Preparing the api wrapper
api = API(auth)

# Request a Twitter user to search. Default will be @GilesHC
twitterusername = raw_input("Who do you want to check out? ") or 'GilesHC'
s = Tweep(twitterusername)
s.converse()
s.tcontent()
s.top_mentions()
s.top_replies()
s.top_hashtags()
s.context_tweets()
s.mongo_filler()