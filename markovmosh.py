#!/usr/bin/python2
import random
import re
import redis
import argparse

# based on coleifer's irc bot. will be modifying moar

class Markov():
        separator = '\x01'
        stop_word = '\x02'
        print_red = '\x1b[31m'
        print_green = '\x1b[32m'
        print_yellow = '\x1b[33m'
        print_reset = '\x1b[39;49m'
        input_corpus = ["minified-samples/36.txt","samples/udhr.txt","samples/gtfts.txt","samples/soc.txt","samples/sscb.txt"]
        _inactive = ["../log.txt","minified-samples/lo.txt","minified-samples/bi.txt","minified-samples/li.txt"]
        
        def __init__(self, max_words, gen_limit, chain_length = 2):
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
                for i in range(self.max_words):
                    words = key.split(self.separator)
                    gen_words.append(words[0])
                    next_word = self.redis_conn.srandmember(key)
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

        def go(self,user_input):
                if user_input == "random":
                    random = self.redis_conn.randomkey()
                    return self.generate(random)
                else:
                    words = user_input.split()
                    if len(words) > self.chain_length:
                        key = words[-self.chain_length:]
                        return ' '.join(words[:-self.chain_length]) + " " + self.generate(self.separator.join(key))
                    else:
                        return self.generate(self.separator.join(user_input.split()))

        def search(self,query):
            return self.redis_conn.keys(query)

        def flush(self):
            self.redis_conn.flushall()

        def train(self,filenames):
            # pass in filenames as a list. I'll read all of 'em
            for path in filenames:
                with open(path,"r") as f:
                    print "{yellow}[::]{reset} Reading {path}, parsing into redis. May take a while depending on your filesize.".format(yellow=self.print_yellow,reset=self.print_reset,path=path)
                    self.read(f)
                    print "{green}[::]{reset} Successfully read {path}!".format(green=self.print_green,reset=self.print_reset,path=path)

def main():
    p = argparse.ArgumentParser(description="Create and train a markov-chain based text wrangler. Assumes a running redis instance on localhost")
    p.add_argument("-s", "--seed", help="a $chain-length word phrase to seed the generator with. defaults to random")
    p.add_argument("-t", "--train", help="specify a file to train the text generator with", nargs='+')
    p.add_argument("-k", "--key", help="search for a key in the redis store")
    p.add_argument("-f", "--flush", help="drop all keys in the redis store, start again with training", action="store_true")
    p.add_argument("-m", "--max-words", help="the most words that will be generated in a resulting message", default=30)
    p.add_argument("-g", "--gen-limit", help="the most messages that the generator will select from", default=100)
    args = p.parse_args()

    m = Markov(int(args.max_words),int(args.gen_limit))

    if args.key:
        for item in m.search(args.key):
            print ' '.join(item.split(m.separator))
    elif args.flush:
        m.flush()
    elif args.train:
        m.train(args.train)
    elif args.seed:
        print m.go(args.seed)
    else:
        print m.go("random")

if (__name__=='__main__'):
    main()
