import praw
import nltk
from nltk import *
import requests
from wordnik import *
from nltk.corpus import wordnet
import pprint
import string

MAX_QUERY_LENGTH = 3
UD_URL = 'http://api.urbandictionary.com/v0/define'
WK_URL = 'http://api.wordnik.com/v4'
WK_API_KEY = 'c637dbc760f763ad2300e03d5310e3da0dd03c6748e1df8ee'
DEBUG_QUERY = ''
NOT_ALLOWED = (',', '.', '!', '?')

def setup():
    r = praw.Reddit('Urban Dictionary Bot by u/fr023nske7ch')
    r.login('Urban-Dictionary-Bot', 'blumpkin4u')
    wk_client = swagger.ApiClient(WK_API_KEY, WK_URL)
    word_api = WordApi.WordApi(wk_client)
    nltk.data.path.append('./nltk_data/')
    return (r, word_api)

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
            while end < len(tokens) and end - i <= MAX_QUERY_LENGTH:
                i = tokens.index(start)
                while i < end and end - i <= MAX_QUERY_LENGTH:
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
                    print "About to check if following phrase exists in english: " + query  
                    ex_result = function(query, *args)
                    if not ex_result:
                        print "Now checking if exists in urban dictionary"
                        ud_result = urban_dictionary(query)
                        if ud_result.json().get(u'list'):
                            print "Found interesting phrase: " + query
                            interesting_phrases[query] = ud_result.json()
                            interesting_phrases_list.append(query) 
                            count += 1
                    prev_queries.append(query)
                i += 1
            query_list = []
            end += 1    

    print count
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(interesting_phrases_list)
    pp.pprint(interesting_phrases)

def urban_dictionary(query):
    payload = {"term": query}
    result = requests.get(UD_URL, params=payload)
    if query == DEBUG_QUERY:
        print result.url
        print result.json()
    return result

def wordnik(query, word_api):
    result = word_api.getDefinitions(query, useCanonical='true')
    if query == DEBUG_QUERY:
        print result[0].text
    return result

def wordnet_check(query):
    if not wordnet.synsets(query):
      return None
    else:
      return wordnet.synsets(query)

def tokenize(comment):
    comment_str = comment.body.encode("ascii")
    tokens = WordPunctTokenizer().tokenize(comment_str)
    print tokens
    for prev, item, next in list(neighborhood(tokens)):
        if prev:
            print "prev: " + prev
        if item:
            print "item: " + item
        if next:
            print "next: " + next

        # Checks if the previous token and the next token are letters if this token is '
        if item == "'" and re.match('^[a-zA-Z]+$', prev) and re.match('^[a-zA-Z]+$', next):
            contraction = [prev, item, next]
            i = tokens.index(item)
            tokens[i] = ''.join(contraction)
            print "New token: " + tokens[i]
            tokens.remove(prev)
            tokens.remove(next)

        if item in NOT_ALLOWED:
            print "Removing: " + item
            tokens.remove(item)

        print ""

    print "Cleaned tokens:"
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(tokens)

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


(r, word_api) = setup()
# submission = r.get_submission("http://www.reddit.com/r/nfl/comments/1n1tw1/49ers_qb_kaepernick_favorites_the_hate_messages/ccfhhz2")
# submission = r.get_submission("http://www.reddit.com/r/opiates/comments/1nhfg0/quick_question_regarding_different_terms_for/cciqznb")
# submission = r.get_submission("http://www.reddit.com/r/leagueoflegends/comments/1ngkwg/why_having_friends_in_1_or_more_lower_divisions/ccirgdm")
# submission = r.get_submission("http://www.reddit.com/r/pics/comments/1od06f/the_most_unexplained_photos_that_exist_w/ccr6mt9")
submission = r.get_submission("http://www.reddit.com/r/depression/comments/1nfxka/boyfriend_is_on_a_downswing_told_me_about_it_out/ccrc80f")
flat_comments = submission.comments
# brute_force(flat_comments)
# query_limit(flat_comments)
import time
start = time.time()
tokens = tokenize(flat_comments[0])
print "tokenize took", time.time() - start, "seconds."
start = time.time()
compare_with_external(tokens, wordnik, word_api)
print "comparing with wordnik took", time.time() - start, "seconds."
start = time.time()
compare_with_external(tokens, wordnet_check)
print "comparing with wordnet took", time.time() - start, "seconds."