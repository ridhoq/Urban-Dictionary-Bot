import praw
import nltk
import requests
import json

MAX_QUERY_LENGTH = 5
UD_URL = "http://api.urbandictionary.com/v0/define"

def setup():
    r = praw.Reddit('Urban Dictionary Bot by u/fr023nske7ch')
    r.login('Urban-Dictionary-Bot', 'blumpkin4u')
    # submission = r.get_submission(submission_id='1mwf1y')
    return r

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
                count += 1
                if query != "":
                    print "About to make query: " + query
                    urban_dictionary(query)
                query_list = []
    print count

def urban_dictionary(query):
    payload = {"term": query}
    r = requests.get(UD_URL, params=payload)
    print r.json()


r = setup()
submission = r.get_submission("http://www.reddit.com/r/nfl/comments/1n1tw1/49ers_qb_kaepernick_favorites_the_hate_messages/ccfhhz2")
flat_comments = submission.comments
# brute_force(flat_comments)
query_limit(flat_comments)
# urban_dictionary("")