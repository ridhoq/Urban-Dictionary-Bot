import praw
from nltk import *
import requests
import json
from wordnik import *

MAX_QUERY_LENGTH = 5
UD_URL = 'http://api.urbandictionary.com/v0/define'
WK_URL = 'http://api.wordnik.com/v4'
WK_API_KEY = 'c637dbc760f763ad2300e03d5310e3da0dd03c6748e1df8ee'
DEBUG_QUERY = ''

def setup():
    r = praw.Reddit('Urban Dictionary Bot by u/fr023nske7ch')
    r.login('Urban-Dictionary-Bot', 'blumpkin4u')
    wk_client = swagger.ApiClient(WK_API_KEY, WK_URL)
    word_api = WordApi.WordApi(wk_client)
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

def compare_with_english_dictionary(flat_comments, word_api):
    already_done = set()
    count = 0
    for comment in flat_comments:
        tokens = tokenize(comment)
        print tokens
        prev_queries = []
        interesting_phrases = {}
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
                        print "About to make query: " + query
                        ud_result = urban_dictionary(query)
                        wk_result = wordnik(query, word_api)
                        if ud_result.json().get(u'list') and not wk_result:
                            print "Found interesting phrase: " + query
                            interesting_phrases[query] = ud_result.json()
                            count += 1
                        prev_queries.append(query)
                    i += 1
                query_list = []
                end += 1    

    print count
    print interesting_phrases

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

def tokenize(comment):
    print comment.body
    print type(comment.body)
    comment_str = comment.body.encode("ascii")
    print type(comment_str)
    print comment_str
    tokens = WordPunctTokenizer().tokenize(comment_str)
    print tokens
    for prev, item, next in neighborhood(tokens):
        if item == "'" and re.match('^[a-zA-Z]+$', prev) and re.match('^[a-zA-Z]+$', next):
            contraction = [prev, item, next]
            i = tokens.index(item)
            tokens[i] = ''.join(contraction)
            tokens.remove(prev)
            tokens.remove(next)

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
submission = r.get_submission("http://www.reddit.com/r/leagueoflegends/comments/1ngkwg/why_having_friends_in_1_or_more_lower_divisions/ccirgdm")
flat_comments = submission.comments
# brute_force(flat_comments)
# query_limit(flat_comments)
# tokenize(flat_comments[0])
compare_with_english_dictionary(flat_comments, word_api)
# urban_dictionary("")