#!/usr/bin/python2
import random
import re
import redis
import sys
import argparse

# based on coleifer's irc bot. will be modifying moar

class Markov():
    separator = '\x01'
    stop_word = '\x02'
    
    def __init__(self, chain_length = 2, max_words = 30, gen_limit = 100):
        self.redis_conn = redis.Redis()
        self.chain_length = chain_length
        self.max_words = max_words
        self.gen_limit = gen_limit
    
    def make_key(self, k):
        return self.separator.join(k)
    
    # TODO: Can use some more things to sanitize out, maybe code and markup
    def sanitize_message(self, message):
        return re.sub('[\"\',]', '', message.lower())

    def split_message(self, message):
        # split the incoming message into words, i.e. ['what', 'up', 'bro']
        words = message.split()
        # if the message is any shorter, it won't lead anywhere
        if len(words) > self.chain_length:
            words.append(self.stop_word) 
            for i in range(len(words) - self.chain_length):
                yield words[i:i + self.chain_length + 1]
    
    def generate_message(self, seed):
        key = seed
        gen_words = []
        for i in xrange(self.max_words):
            words = key.split(self.separator)
            gen_words.append(words[0])
            next_word = self.redis_conn.srandmember(self.make_key(key))
            if not next_word:
                break
            key = self.separator.join(words[1:] + [next_word])
        return ' '.join(gen_words)

    def read(self,f):
      # read in an open fd, add all lines to the redis store
      for line in f:
        for words in self.split_message(self.sanitize_message(line)):
            # grab everything but the last word
            key = words[:-1]
            # add the last word to the set
            self.redis_conn.sadd(self.make_key(key), words[-1])

    def generate(self,key):
      # iterate through gen_limit rounds, pick a random choice from long ones
      best_message = ''
      messages = []
      for i in range(self.gen_limit):
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
      with open("minified-samples/36.txt","r") as f: # wu-tang clan 36 chambers
        self.read(f)
      with open("samples/udhr.txt","r") as f: # universal declaration of human rights
        self.read(f)
      #with open("minified-samples/bi.txt","r") as f: # bible, king james
      #  self.read(f)
      with open("samples/gtfts.txt","r") as f: # go the fuck to sleep
        self.read(f)
      with open('samples/soc.txt','r') as f: # straight outta compton
        self.read(f)
      #with open('../log.txt','r') as f: # my irc logs
      #  self.read(f)
      with open('samples/sscb.txt','r') as f: # shell scripting cookbook
        self.read(f)

      #with open("minified-samples/lo.txt","r") as f:
      #  m.read(f)
      #with open("minified-samples/li.txt","r") as f:
      #  m.read(f)
            
#p = argparse.ArgumentParser(description="create and train a markov text wrangler")
#p.add_argument("board", help="the craigslist board you want to scrape", choices=BOARDLIST)
#p.add_argument("-l", "--location", help="show location along with post title", action="store_true")
#p.add_argument("-p", "--price", help="show price along with post title", action="store_true")
#p.add_argument("-n", "--number", type=int, help="number of posts you want (be reasonable). defaults to 100", default=100)
#args = p.parse_args()

m = Markov()
m.setup()
#m.go(sys.argv[1])
