import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

c = MongoClient()
db = c.BTdb
Gawk = db.gwker
Gawk.remove()

# Visit a list of Gawker sites to begin the process!
gLinks = ['http://gizmodo.com', 'http://io9.com', 'http://jezebel.com', 'http://lifehacker.com', 'http://deadspin.com', 'http://sploid.gizmodo.com', 'http://valleywag.gawker.com/']
site_class = ['gadgets & technology', 'science & science fiction', "celebrity, sex & womens fashion", 'productivity tips', 'sports', 'news, futuristic ideas & technology', 'Silicon Valley gossip']
for i, gl in enumerate(gLinks):
    links = []
    gawker = requests.get(gl)
    gawker = gawker.text
    sopa = BeautifulSoup(gawker)

    # Locate the links to the main articles on the gawker site.
    s = sopa.find_all('h1')
    # Create a dictionary with the article title and link for each article highlighed on the Gawker site.
    for item in s:
            Lholder = {}
            Lholder['title'] = item.find('a').string
            Lholder['link'] = item.find('a').get('href')
            links.append(Lholder)

    # Scrape article text from each link captured above.
    for n in links:
        url = n['link']
        url = requests.get(url)
        url = url.text 
        soup = BeautifulSoup(url)
        a_text = ""
        for p in soup.find_all('p'):
            for s in p:
                try:
                    for st in s.string.rstrip().replace(".", " ").replace("?", " ").lower().decode('unicode_escape').encode('ascii', 'ignore'):
                        a_text += st
                except:
                    pass
        
        Gawk.insert({"title": n['title'],
                     "url": n['link'],
                     "class": site_class[i],
                     "text": a_text})
print "Success!"