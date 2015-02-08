#!/usr/bin/python
import random
import re
import redis
import sys
import argparse

class Markov():
    chain_length = 2
    max_words = 30
    separator = '\x01'
    stop_word = '\x02'
    messages_to_generate = 100
    
    def __init__(self, *args, **kwargs):
        self.redis_conn = redis.Redis()
    
    def make_key(self, k):
        return '-'.join(k)
    
    def sanitize_message(self, message):
        return re.sub('[\"\']', '', message.lower())

    def split_message(self, message):
        # split the incoming message into words, i.e. ['what', 'up', 'bro']
        words = message.split()
        # if the message is any shorter, it won't lead anywhere
        if len(words) > self.chain_length:
            # add some stop words onto the message
            # ['what', 'up', 'bro', '\x02']
            words.append(self.stop_word) 
            # len(words) == 4, so range(4-2) == range(2) == 0, 1, meaning
            # we return the following slices: [0:3], [1:4]
            # or ['what', 'up', 'bro'], ['up', 'bro', '\x02']
            for i in range(len(words) - self.chain_length):
                yield words[i:i + self.chain_length + 1]
    
    def generate_message(self, seed):
        key = seed
        
        # keep a list of words we've seen
        gen_words = []
        
        # only follow the chain so far, up to <max words>
        for i in xrange(self.max_words):
        # split the key on the separator to extract the words -- the key
            # might look like "this\x01is" and split out into ['this', 'is']
            words = key.split(self.separator)
            
            # add the word to the list of words in our generated message
            gen_words.append(words[0])
            
            # get a new word that lives at this key -- if none are present we've
            # reached the end of the chain and can bail
            next_word = self.redis_conn.srandmember(self.make_key(key))
            if not next_word:
                break
            
            # create a new key combining the end of the old one and the next_word
            key = self.separator.join(words[1:] + [next_word])

        return ' '.join(gen_words)

    def read(self,f):
      for line in f:
        for words in self.split_message(self.sanitize_message(line)):
            # grab everything but the last word
            key = self.separator.join(words[:-1])
            # add the last word to the set
            self.redis_conn.sadd(self.make_key(key), words[-1])

    def generate(self,key):
      best_message = ''
      messages = []
      for i in range(self.messages_to_generate):
        generated = self.generate_message(seed=key)
        if len(generated) > len(best_message):
          best_message = generated
        if best_message:
          messages.append(best_message)

      if len(messages):
        return random.choice(messages)

    def run(self):
      while True:
        user_input = raw_input("? ")
        if user_input == "random":
          random = self.redis_conn.randomkey()
          key = ''.join(random.split('-'))
          print self.generate(key)
          continue
        words = user_input.split()
        if len(words) > self.chain_length:
          key = words[-self.chain_length:]
          print ' '.join(words[:-self.chain_length]) + " " + self.generate('\x01'.join(key))
        else:
          print self.generate('\x01'.join(user_input.split()))

    def go(self,user_input):
        if user_input == "random":
          random = self.redis_conn.randomkey()
          key = ''.join(random.split('-'))
          print self.generate(key)
        else:
          words = user_input.split()
          if len(words) > self.chain_length:
            key = words[-self.chain_length:]
            print ' '.join(words[:-self.chain_length]) + " " + self.generate('\x01'.join(key))
          else:
            print self.generate('\x01'.join(user_input.split()))

    def search(self,query):
      print self.redis_conn.keys(query)

    def setup(self):
      with open("36.txt","r") as f: # wu-tang clan 36 chambers
        self.read(f)
      with open("udhr.txt","r") as f: # universal declaration of human rights
        self.read(f)
      #with open("bi.txt","r") as f: # bible, king james
      #  self.read(f)
      with open("gtfts.txt","r") as f: # go the fuck to sleep
        self.read(f)
      with open('soc.txt','r') as f: # straight outta compton
        self.read(f)
      #with open('log.txt','r') as f: # my irc logs
      #  self.read(f)
      with open('sscb.txt','r') as f: # shell scripting cookbook
        self.read(f)

      #with open("lo.txt","r") as f:
      #  m.read(f)
      #with open("li.txt","r") as f:
      #  m.read(f)
            
p = argparse.ArgumentParser(description="create and train a markov text wrangler")
p.add_argument("board", help="the craigslist board you want to scrape", choices=BOARDLIST)
p.add_argument("-l", "--location", help="show location along with post title", action="store_true")
p.add_argument("-p", "--price", help="show price along with post title", action="store_true")
p.add_argument("-n", "--number", type=int, help="number of posts you want (be reasonable). defaults to 100", default=100)
args = p.parse_args()


m = Markov()
#m.setup()
m.go(sys.argv[1])
