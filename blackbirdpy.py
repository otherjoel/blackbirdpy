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
# New features + adaptation for use with Pollen (http://pollenpub.com) by Joel Dueck (@joeld)
#
# See README.md
#
# Requires Python 2.7.
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
import urllib
import pytz
import tweepy
import shutil
import requests

myTZ = pytz.timezone('US/Central')

TWEET_EMBED_POLLEN = u'''◊tweet[#:id "{id}"
       #:handle "{screenName}"
       #:realname "{realName}"
       #:permlink "{tweetURL}"
       #:timestamp "{timeStamp}"]{{{tweetText}}}
'''

TWEET_EMBED_RT_POLLEN = u'''
              ◊retweet[#:id "{id}" #:handle "{screenName}" #:realname "{realName}" #:permlink "{tweetURL}" #:timestamp "{timeStamp}"]{{{tweetText}}}'''

TWEET_EMBED_HTML = u'''<div class="bbpBox" id="t{id}">\n<blockquote>\n<span class="twContent">{tweetText}</span><span class="twMeta"><br /><span class="twDecoration">&mdash; </span><span class="twRealName">{realName}</span><span class="twDecoration"> (</span><a href="http://twitter.com/{screenName}"><span class="twScreenName">@{screenName}</span></a><span class="twDecoration">) </span><a href="{tweetURL}"><span class="twTimeStamp">{timeStamp}</span></a><span class="twDecoration"></span></span>\n</blockquote>\n</div>
'''

# Absolute path to where you want to download local copies of any photo
# contained in the tweet.
IMAGE_FOLDER = '/Users/joel/Documents/code/thenotepad/img/'

# Will be prepended to src attribute of images in embedded tweets
IMAGE_REL = '/img/'

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

def wrap_entities(t,tid):
  """Turn URLs and @ mentions into links. Embed Twitter native photos.
  (Actually downloads a local copy of any photo into the img/ subfolder.)
  """
  text = t.text
  mentions = t.entities['user_mentions']
  hashtags = t.entities['hashtags']
  urls = t.entities['urls']
  # media = json['entities']['media']
  try:
    media = t.extended_entities['media']
  except (KeyError, AttributeError):
    media = []

  for u in urls:
    try:
        tweet_id_from_tweet_url(u['expanded_url']) # will raise ValueError if not a twitter status
        link = embed_quoted_retweet_html(u['expanded_url'])
    except (ValueError, KeyError, TypeError):
        try:
            link = u'◊link["' + u['expanded_url'] + '"]{' + u['display_url'] + '}'
        except (KeyError, TypeError):
            link = u'◊link["' + u['url'] + '"]{' + u['url'] + '}'

    text = text.replace(u['url'], link)

  for m in mentions:
    text = re.sub(u'(?i)@' + m['screen_name'], u'◊link["http://twitter.com/' +
            m['screen_name'] + '"]{@' + m['screen_name'] + '}', text, 0)

  for h in hashtags:
    text = re.sub('(?i)#' + h['text'], u'◊link["http://twitter.com/search/%23' +
            h['text'] + u'"]{#' + h['text'] + u'}', text, 0)

  # For some reason, multiple photos have only one URL in the text of the tweet.
  if len(media) > 0:
    photolink = ''
    for m in media:
      if m['type'] == 'photo':
        imgfile = 'tweet-' + tid + '.' + m['media_url'].split('.')[-1]
        imgfile = download_image(m['media_url'] + ':large', IMAGE_FOLDER, imgfile)
        photolink += u'◊image["' + IMAGE_REL + imgfile + '"]'
        #photolink += u'◊link["' + m['media_url'] + ':large"]{' +\
        #            '<img src="' + m['media_url'] + ':small">}'
      else:
        photolink += u'◊link["' + m['expanded_url'] + '"]{' +\
                    m['display_url'] + '}'
    text = text.replace(m['url'], photolink)

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
    tweet_text = wrap_entities(tweet,tweet_id)
    #tweet_text = wrap_entities(tweet).replace('\n', '<br />')

    tweet_created_datetime = pytz.utc.localize(tweet.created_at).astimezone(myTZ)
    tweet_timestamp = tweet_created_datetime.strftime("%b %-d %Y %-I:%M %p")

    if extra_css is None:
        extra_css = {}

    html = TWEET_EMBED_POLLEN.format(
        id=tweet_id,
        tweetURL=tweet_url,
        screenName=tweet.user.screen_name,
        realName=tweet.user.name,
        tweetText=tweet_text,
        source=tweet.source,
        #profilePic=tweet.user.profile_image_url,
        #profileBackgroundColor=tweet.user.profile_background_color,
        #profileBackgroundImage=tweet.user.profile_background_image_url,
        #profileTextColor=tweet.user.profile_text_color,
        #profileLinkColor=tweet.user.profile_link_color,
        timeStamp=tweet_timestamp,
        utcOffset=tweet.user.utc_offset
        # bbpBoxCss=extra_css.get('bbpBox', ''),
    )
    return html

def embed_quoted_retweet_html(tweet_url):
    """Generate embedded HTML for a tweet-within-a-tweet, given its Twitter URL.
    """
    tweet_id = tweet_id_from_tweet_url(tweet_url)
    api = setup_api()
    tweet = api.get_status(tweet_id)

    tweet_created_datetime = pytz.utc.localize(tweet.created_at).astimezone(myTZ)
    tweet_timestamp = tweet_created_datetime.strftime("%b %-d %Y %-I:%M %p")

    html = TWEET_EMBED_RT_POLLEN.format(
        id=tweet_id,
        tweetURL=tweet_url,
        screenName=tweet.user.screen_name,
        realName=tweet.user.name,
        tweetText=tweet.text,
        source=tweet.source,
        timeStamp=tweet_timestamp,
        utcOffset=tweet.user.utc_offset
    )
    return html

def stat(str):
    print ("[%s] %s" % (datetime.now().strftime("%X"),str))

def download_image(image_url, foldername, fname):
    """
    Downloads an image over HTTP and saves it in the specified folder.
    Returns the filename of the saved image file.
    """

    #stat("Downloading image at {0}, saving as {1}".format(image_url,fname))
    response = requests.get(image_url, stream=True)

    if response.status_code == 200:
        m = re.search('[^/]+\.(png|jpg|gif|jpeg|bmp|tiff)$',fname,re.IGNORECASE)
        if m is None:
            stat("(BAD LINK, no extension: %s )" % fname)
            return "BAD LINK:"+fname

        filename = urllib.unquote(m.group(0)).lower()
        filename = filename.split('.')[0] + "." + filename.split('.')[-1]
        filename = re.sub(r'[^a-zA-Z0-9\-\.]','', filename)

        # Uncomment this bit if you need to ensure you don’t overwrite an
        # existing file of the same name.
        #temp_filename = filename
        #x = 2
        #while os.path.isfile(os.path.join(foldername,temp_filename)):
        #    file_parts = filename.split('.')
        #    temp_filename = file_parts[0] + ("%02d" % x) + "." + file_parts[-1]
        #    x += 1
        #
        #filename = temp_filename

        #stat("(Response GOOD, image has filename: %s )" % filename)

        if not os.path.exists(foldername):
			os.makedirs(foldername)

        with open(os.path.join(foldername,filename), 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
    else:
        filename = "BAD HTTP response: "+image_url
        #stat(filename)

    del response
    return filename

if __name__ == '__main__':
    print embed_tweet_html(sys.argv[1]).encode('utf8')
