import praw
import nltk
from nltk import *
import requests
from wordnik import *
from nltk.corpus import wordnet
import pprint
import string
import ConfigParser
import logging, logging.handlers

MAX_QUERY_LENGTH = 2
UD_URL = 'http://api.urbandictionary.com/v0/define'
WK_URL = 'http://api.wordnik.com/v4'
DEBUG_QUERY = ''
NOT_ALLOWED = ('http', '://')

def setup():
    setup_logging()
    config = ConfigParser.RawConfigParser()
    config.read('setup.cfg')
    USER = config.get('setup', 'USER')
    PASSWORD = config.get('setup', 'PASSWORD')
    r = praw.Reddit('Urban Dictionary Bot by u/fr023nske7ch')
    r.login(USER, PASSWORD)
    WK_API_KEY = config.get('setup', 'WK_API_KEY')
    wk_client = swagger.ApiClient(WK_API_KEY, WK_URL)
    word_api = WordApi.WordApi(wk_client)
    nltk.data.path.append('./nltk_data/')
    return (r, word_api)

def setup_logging():
    logger = logging.getLogger('udb')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('udb.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # smtp_handler = logging.handlers.SMTPHandler('127.0.0.1:25', 'error@udb.com', 'ridwanhoq@gmail.com', 'UDB ERROR!')
    # smtp_handler.setLevel(logging.ERROR)
    # smtp_handler.setFormatter(formatter)
    # logger.addHandler(smtp_handler)

def brute_force(flat_comments):
    already_done = set()
    count = 0
    for comment in flat_comments:
        tokens = nltk.word_tokenize(comment.body)
        for start in tokens:
            end = tokens.index(start) + 1
            query_list = []
            while end < len(tokens):
                i = tokens.index(start)
                while i < end:
                    query_list.append(tokens[i])
                    i += 1
                end += 1    
                query = ' '.join(query_list)
                count += 1
                print query
                query_list = []
    print count

def query_limit(flat_comments):
    already_done = set()
    count = 0
    for comment in flat_comments:
        tokens = nltk.word_tokenize(comment.body)
        prev_queries = []
        for start in tokens:
            i = tokens.index(start)
            end = i + 1
            query_list = []
            while end < len(tokens) and end - i < MAX_QUERY_LENGTH:
                i = tokens.index(start)
                while i < end and end - i < MAX_QUERY_LENGTH:
                    query_list.append(tokens[i])
                    i += 1
                end += 1    
                query = ' '.join(query_list)
                if query != "" and query not in prev_queries:
                    print "About to make query: " + query
                    urban_dictionary(query)
                    count += 1
                    prev_queries.append(query)
                query_list = []
    print count

def compare_with_external(tokens, function, *args):
    logger = logging.getLogger('udb')
    count = 0
    prev_queries = []
    interesting_phrases = {}
    interesting_phrases_list = []
    for start in tokens:
        i = tokens.index(start)
        end = i + 1
        query_list = []
        while end < len(tokens) and end - i <= MAX_QUERY_LENGTH:
            i = tokens.index(start)
            while i <= end and end - i <= MAX_QUERY_LENGTH:
                query_list.append(tokens[i])
                query = ' '.join(query_list)
                if query != "" and query not in prev_queries:
                    logger.info("About to check if following phrase exists in english: " + query)  
                    ex_result = function(query, *args)
                    if not ex_result:
                        logger.info("Now checking if exists in urban dictionary")
                        ud_result = urban_dictionary(query)
                        if ud_result.json().get(u'list'):
                            logger.info("****FOUND INTERESTING PHRASE****  " + query)
                            interesting_phrases[query] = ud_result.json()
                            interesting_phrases_list.append(query) 
                            count += 1
                    prev_queries.append(query)
                i += 1
            query_list = []
            end += 1    

    logger.info("Interesting phrases list: " + pprint.pformat(interesting_phrases_list))
    logger.info("interesting phrases (full dict): " + pprint.pformat(interesting_phrases))
    return interesting_phrases

def urban_dictionary(query):
    payload = {"term": query}
    result = requests.get(UD_URL, params=payload)
    return result

def wordnik(query, word_api):
    result = word_api.getDefinitions(query, useCanonical='true')
    return result

def wordnet_check(query):
    if not wordnet.synsets(query):
      return None
    else:
      return wordnet.synsets(query)

def tokenize(comment):
    logger = logging.getLogger('udb')
    comment_str = comment.body
    tokens = WordPunctTokenizer().tokenize(comment_str)
    logger.info("Tokens (before cleaning): " + str(tokens))
    for prev, item, next in list(neighborhood(tokens)):
        found_contraction = False
        if item == "'" and re.match('^[a-zA-Z]+$', prev) and re.match('^[a-zA-Z]+$', next):
            contraction = [prev, item, next]
            i = tokens.index(item)
            tokens[i] = ''.join(contraction)
            logger.info("New token: " + tokens[i])
            tokens.remove(prev)
            tokens.remove(next)
            found_contraction = True

        if item in string.punctuation or item in NOT_ALLOWED:
            if not found_contraction:
                logger.info("Removing: " + item)
                tokens.remove(item)

    
    logger.info("Cleaned tokens: " + pprint.pformat(tokens))

    return tokens

def neighborhood(iterable):
    iterator = iter(iterable)
    prev = None
    item = iterator.next()  # throws StopIteration if empty.
    for next in iterator:
        yield (prev,item,next)
        prev = item
        item = next
    yield (prev,item,None)

def reply(r, comment, interesting_phrases):
    newline = "\n\n"
    reply = "I found " + str(len(interesting_phrases.keys())) + " words/phrases defined by Urban Dictionary in this comment!" + newline + "***" + newline
    for phrase in interesting_phrases:
        reply += ("[" + phrase + "](" + interesting_phrases[phrase]['list'][0]['permalink'] + "): " + interesting_phrases[phrase]['list'][0]['definition'] + newline)
        for line in interesting_phrases[phrase]['list'][0]['example'].splitlines():
            reply += (">*" + line + "*" + newline)
        reply += ("***" + newline)
    reply += "If you have any questions about me, you can [message me](http://www.reddit.com/message/compose/?to=Urban-Dictionary-Bot) or post on /r/UrbanDictionaryBot."
    comment.reply(reply)


(r, word_api) = setup()
logger = logging.getLogger('udb')
comments = user.get_comments(limit=100)
while True:
    comments = r.get_comments('all', limit='500')
    for comment in comments:
        try:
            import time
            start = time.time()
            tokens = tokenize(comment)
            start = time.time()
            interesting_phrases = compare_with_external(tokens, wordnik, word_api)
            logger.info("TIME TO PROCESS: " + str(time.time() - start))
            if interesting_phrases:
                logger.info("ABOUT TO REPLY!!!")
                reply(r, comment, interesting_phrases)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            logger.exception('')