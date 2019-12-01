import collections
import datetime
import os
import time
import uuid

import bottle
from feedgen import feed
import twitter

TWEET_CREATED_AT_FORMAT = '%a %b %d %H:%M:%S %z %Y'

api_key = os.environ.get("TIS_API_KEY", "")
api_secret = os.environ.get("TIS_API_SECRET", "")
access_token_key = os.environ.get("TIS_TOKEN_KEY", "")
access_token_secret = os.environ.get("TIS_TOKEN_SECRET", "")

uuid_namespace = uuid.UUID('e8cd8531-a8df-4b41-a249-479d15252349')

t = twitter.Twitter(
    auth=twitter.OAuth(access_token_key,
                       access_token_secret,
                       api_key,
                       api_secret))


class RateLimiter(object):
    def __init__(self, max_rate=3, time_unit=1):
        self.time_unit = time_unit
        self.deque = collections.deque(maxlen=max_rate)

    def __call__(self):
        if self.deque.maxlen == len(self.deque):
            cTime = time.time()
            if cTime - self.deque[0] > self.time_unit:
                self.deque.append(cTime)
                return False
            else:
                return True
        self.deque.append(time.time())
        return False


cached_output = None
rate_limiter = RateLimiter(2, 10)


def create_rss_feed_xml():
    tweets = t.statuses.home_timeline(tweet_mode='extended')
    fg = feed.FeedGenerator()
    fg.id('https://twitter.com/omeranson')
    fg.title('Twitter feed')
    fg.subtitle('Twitter timeline')
    fg.link(href='https://twitter.com')
    fg.link(href='http://ansonet.no-ip.biz:8081/feed.xml', rel='self')
    fg.language('en')
    for tweet in tweets:
        fe = fg.add_entry()
        fe.id('https://twitter.com/i/status/%s' % (tweet['id_str']))
        fe.title('%s (@%s)' % (tweet['user']['name'],
                               tweet['user']['screen_name']))
        fe.link(href='https://twitter.com/i/status/%s' % (tweet['id_str']))
        fe.content(_get_tweet_text(tweet), type='html')
        fe.author(name=tweet['user']['name'])
        fe.updated(datetime.datetime.strptime(tweet['created_at'],
                                              TWEET_CREATED_AT_FORMAT))
    output = fg.atom_str(pretty=True)
    global cached_output
    cached_output = output
    return output


def _get_tweet_text(tweet):
    return _escape_html(tweet['full_text']).replace('\n', '<br/>\n')


def _escape_html(text):
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('\'', '&apos;')
                .replace('"', '&quot;'))


@bottle.route('/')
@bottle.route('/feed.xml')
def feed_xml():
    data = create_rss_feed_xml()
    bottle.response.content_type = 'application/xml'
    return data


def main():
    bottle.run(host='0.0.0.0', port=8081)


if __name__ == '__main__':
    main()
