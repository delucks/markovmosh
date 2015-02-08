import requests
from bs4 import BeautifulSoup
from urlparse import urljoin

#baseurl = "http://genius.com/artists/songs?for_artist_page=107&id=Lil-jon&page={pagenum}"
#for i in range(10):
#  r = requests.get(baseurl.format(pagenum=i))
#  soup = BeautifulSoup(r.text)
#  for item in soup.find_all('a','song_link'):
#      print item.get('href')

with open('lyrics','r') as jon:
  data = jon.read()
  soup = BeautifulSoup(data)
  for item in soup.find_all('div','lyrics'):
    print item.text
