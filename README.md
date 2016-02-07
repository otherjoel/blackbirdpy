Blackbirdpy is a set of scripts and styles for quickly embedding "live" tweets in blog posts or other web articles. All links within the tweet, including URLS, screen names, and hashtags are fully clickable. It accesses the Twitter API, but does no user tracking, cookie planting, or other sketchy business.

There are three parts to blackbirdpy:

1. A Python script that takes a tweet's URL as its command-line argument and returns a chunk of HTML for embedding. The HTML puts the tweet in a `<blockquote>` structure and is intended to look decent in an RSS reader.
2. A CSS file that styles the elements of the embedded tweet.
3. An AppleScript that gets the URL of the frontmost Safari window and passes it to the Python script, returning the HTML chunk. I use this in a TextExpander snippet, so I can simply type `;tweet` in my text editor and insert the HTML chunk into the article I'm writing.

The idea is to provide an embedded tweet that looks like a tweet (without the follow, favorite, retweet, etc. buttons) and which degrades to a simple quotation when viewed in RSS.

**This copy was forked from DrDrang’s project in order to add new functionality:**

 * If the tweet contains a retweet, that retweeted tweet is fetched and embedded along with the main tweet.
 * If there is a photo in the tweet, the script downloads a local copy of that, too.
 * Spits out [Pollen](http://pollenpub.com) markup instead of HTML (but I’ve left most of the original code for HTML code intact in case you want to use it.)

Here's an example, which sort of matches what you'd see in an RSS reader:

<div class="bbpBox" id="t223636441371115520"><blockquote><span class="twContent">Embedded tweets don’t have to be fragile or track cookies: <a href="http://www.leancrew.com/all-this/2012/07/good-embedded-tweets/">leancrew.com/all-this/2012/…</a></span><span class="twMeta"><br /><span class="twDecoration">&nbsp;&nbsp;&mdash; </span><span class="twRealName">Dr. Drang</span><span class="twDecoration"> (</span><a href="http://twitter.com/drdrang"><span class="twScreenName">@drdrang</span></a><span class="twDecoration">) </span><a href="https://twitter.com/drdrang/status/223636441371115520"><span class="twTimeStamp">Thu Jul 12 2012 11:34 PM CDT</span></a><span class="twDecoration"></span></span></blockquote></div>

If you follow the link in the tweet, you'll see several tweets.

Blackbirdpy was forked from [Dr Drang’s project][3], which was forked from [Jeff Miller's project][1], , which was, in turn, inspired by [Robin Sloan's Blackbird Pie][2], a JavaScript tool for embedding tweets that Twitter seems to have removed in favor of a more complicated embedding code that I don't like the look of.


[1]: http://github.com/jmillerinc/blackbirdpy
[2]: http://techcrunch.com/2010/05/04/twitter-blackbird-pie/
[3]: https://github.com/drdrang/blackbirdpy
