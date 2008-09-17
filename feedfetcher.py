# coding=utf-8
import feedparser

import ConfigParser
import logging
import md5
import os
import pickle
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('GSFeedParser.feedfetcher')

MINIMUM_INTERVAL = 900 # seconds
CONFIGPATH='/opt/groupserver-1.0-alpha/var/instance/groupserver.data/groupserver.GSFeedParser.config'
DATAPATH='/opt/groupserver-1.0-alpha/var/instance/groupserver.data/groupserver.GSFeedParser.data'

config = ConfigParser.ConfigParser()

config_filenames = map(lambda x: os.path.join(CONFIGPATH, x),
                                 os.listdir(CONFIGPATH))

feed_config = {}

for filename in config_filenames:
    config.read(filename)
    for section in config.sections():
        try:
            interval = config.getint(section, 'interval')
            if interval < MINIMUM_INTERVAL:
                interval = MINIMUM_INTERVAL
        except (ConfigParser.NoOptionError, ValueError):
            logger.error('No interval found in section "%s", file "%s"' % (section, filename))
            interval = MINIMUM_INTERVAL # seconds
        
        try:
            url = config.get(section, 'url')
        except (ConfigParser.NoOptionError):
            logger.error('No URL found in section "%s", file "%s"' % (section, filename))
            pass
        
        if feed_config.has_key(url):
            if feed_config[url]['interval'] > interval:
                feed_config[url]['interval'] = interval
        else:
            feed_config[url] = {'interval': interval,
                                'md5': md5.new(url).hexdigest()}

for url in feed_config:
    out_filename = os.path.join(DATAPATH, feed_config[url]['md5'])
    out_filename_temp = out_filename+'.tmp'
    
    last_modified = None
    last_etag = None
    if os.path.exists(out_filename):
        last_updated = time.time() - os.path.getmtime(out_filename)
        
        if last_updated < feed_config[url]['interval']:
            logger.info("Skipping fetch of %s, last updated %s seconds ago" % 
                        (url, int(last_updated)))
            continue
        else:
            last_feed = pickle.load(file(out_filename))
            last_modified = last_feed.get('updated', None)
            last_etag = last_feed.get('etag', None)
            
    feed = feedparser.parse(url, etag=last_etag, modified=last_modified, agent="GroupServer.Org FeedFetcher")
    for item in feed['entries']:
        print item.keys()
    if feed.get('status', None) == 304:
        logger.info('Feed "%s" unmodified' % url)
        # rewrite last feed
        feed = last_feed
    if feed['bozo'] and feed.has_key('bozo_exception'):
        logger.error('Error fetching "%s", "%s"' % (url, feed['bozo_exception'].getMessage().strip()))
        del(feed['bozo_exception'])
        
    out_file = file(out_filename_temp, 'w+')
    pickle.dump(feed, out_file)
    os.rename(out_filename_temp, out_filename)
    
    logger.info('Fetched %s' % (url))
    
