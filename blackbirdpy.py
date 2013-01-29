# -*- coding: utf-8 -*-
#
# Blackbirdpy - a Python implementation of Blackbird Pie, the tool
# @robinsloan uses to generate embedded HTML tweets for blog posts.
#
# See: http://media.twitter.com/blackbird-pie
#
# This Python version was written by Jeff Miller, http://twitter.com/jeffmiller
#
# Various formatting changes by Dr. Drang, http://twitter.com/drdrang
#
# Requires Python 2.6.
#
# Usage:
#
# - To generate embedded HTML for a tweet from inside a Python program:
#
#   import blackbirdpy
#   embed_html = blackbirdpy.embed_tweet_html(tweet_url)
#
# - To generate embedded HTML for a tweet from the command line:
#
#   $ python blackbirdpy.py <tweeturl>
#     e.g.
#   $ python blackbirdpy.py http://twitter.com/punchfork/status/16342628623
#


from datetime import datetime, timedelta
import email.utils
import json
import re
import sys
import os
import urllib2
import pytz
import tweepy

myTZ = pytz.timezone('US/Central')

TWEET_EMBED_HTML = u'''<div class="bbpBox" id="t{id}">\n<blockquote>\n<span class="twContent">{tweetText}</span><span class="twMeta"><br /><span class="twDecoration">&mdash; </span><span class="twRealName">{realName}</span><span class="twDecoration"> (</span><a href="http://twitter.com/{screenName}"><span class="twScreenName">@{screenName}</span></a><span class="twDecoration">) </span><a href="{tweetURL}"><span class="twTimeStamp">{timeStamp}</span></a><span class="twDecoration"></span></span>\n</blockquote>\n</div>
'''

# This function pretty much taken directly from a tweepy example.
def setup_api():
  """Authorize the use of the Twitter API."""
  a = {}
  with open(os.environ['HOME'] + '/.twang') as twang:
    for line in twang:
      k, v = line.split(': ')
      a[k] = v.strip()
  auth = tweepy.OAuthHandler(a['consumerKey'], a['consumerSecret'])
  auth.set_access_token(a['token'], a['tokenSecret'])
  return tweepy.API(auth)

def wrap_entities(t):
  """Turn URLs and @ mentions into links. Embed Twitter native photos."""
  text = t.text
  mentions = t.entities['user_mentions']
  hashtags = t.entities['hashtags']
  urls = t.entities['urls']
  # media = json['entities']['media']
  try:
    media = t.entities['media']
  except KeyError:
    media = []
  
  for u in urls:
    try:
      link = '<a href="' + u['expanded_url'] + '">' + u['display_url'] + '</a>'
    except (KeyError, TypeError):
      link = '<a href="' + u['url'] + '">' + u['url'] + '</a>'
    text = text.replace(u['url'], link)
  
  for m in mentions:
    text = re.sub('(?i)@' + m['screen_name'], '<a href="http://twitter.com/' +
            m['screen_name'] + '">@' + m['screen_name'] + '</a>', text, 0)

  for h in hashtags:
    text = re.sub('(?i)#' + h['text'], '<a href="http://twitter.com/search/%23' +
            h['text'] + '">#' + h['text'] + '</a>', text, 0)
  
  for m in media:
    if m['type'] == 'photo':
      link = '<br /><br /><a href="' + m['media_url'] + ':large">' +\
              '<img src="' + m['media_url'] + ':small"></a><br />'
    else:
      link = '<a href="' + m['expanded_url'] + '">' + m['display_url'] + '</a>'
    text = text.replace(m['url'], link)

  return text
    
def tweet_id_from_tweet_url(tweet_url):
    """Extract and return the numeric tweet ID from a full tweet URL."""
    match = re.match(r'^https?://twitter\.com/(?:#!\/)?\w+/status(?:es)?/(\d+)$', tweet_url)
    try:
        return match.group(1)
    except AttributeError:
        raise ValueError('Invalid tweet URL: {0}'.format(tweet_url))


def embed_tweet_html(tweet_url, extra_css=None):
    """Generate embedded HTML for a tweet, given its Twitter URL.  The
    result is formatted as a simple quote, but with span classes that
    allow it to be reformatted dynamically (through jQuery) in the style
    of Robin Sloan's Blackbird Pie.
    See: http://media.twitter.com/blackbird-pie

    The optional extra_css argument is a dictionary of CSS class names
    to CSS style text.  If provided, the extra style text will be
    included in the embedded HTML CSS.  Currently only the bbpBox
    class name is used by this feature.
    """
    tweet_id = tweet_id_from_tweet_url(tweet_url)
    api = setup_api()
    tweet = api.get_status(tweet_id)
    tweet_text = wrap_entities(tweet).replace('\n', '<br />')

    tweet_created_datetime = pytz.utc.localize(tweet.created_at).astimezone(myTZ)
    tweet_timestamp = tweet_created_datetime.strftime("%a %b %-d %Y %-I:%M %p %Z")

    if extra_css is None:
        extra_css = {}

    html = TWEET_EMBED_HTML.format(
        id=tweet_id,
        tweetURL=tweet_url,
        screenName=tweet.user.screen_name,
        realName=tweet.user.name,
        tweetText=tweet_text,
        source=tweet.source,
        profilePic=tweet.user.profile_image_url,
        profileBackgroundColor=tweet.user.profile_background_color,
        profileBackgroundImage=tweet.user.profile_background_image_url,
        profileTextColor=tweet.user.profile_text_color,
        profileLinkColor=tweet.user.profile_link_color,
        timeStamp=tweet_timestamp,
        utcOffset=tweet.user.utc_offset,
        bbpBoxCss=extra_css.get('bbpBox', ''),
    )
    return html



if __name__ == '__main__':
    print embed_tweet_html(sys.argv[1]).encode('utf8')
