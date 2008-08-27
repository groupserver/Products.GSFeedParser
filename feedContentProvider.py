from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.interface import implements, Interface
from zope.component import createObject, adapts, provideAdapter
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.contentprovider.interfaces import IContentProvider, UpdateNotCalled

import Products.GSContent
from Products.XWFCore.cache import LRUCache, SimpleCache
from Products.Five import BrowserView
from Products.XWFCore.XWFUtils import locateDataDirectory

from interfaces import IGSFeedContentProvider

import os
import md5
import ConfigParser

import pickle

import logging

log = logging.getLogger('GSFeedParser')

class GSFeedView(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

class GSFeedConfigReader(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = Products.GSContent.view.GSSiteInfo(self.context)
        self.groupInfo = createObject('groupserver.GroupInfo',
                                      self.context)
        self.siteRoot = self.context.site_root()
        
        self.configId = '%'.join((self.siteRoot.getId(),
                                   self.siteInfo.get_id(),
                                   self.groupInfo.get_id()))
    @property
    def urls(self):
        urls = []
        c = self.config
        for section in c.sections():
            try:
                url = c.get(section, 'url')
                urls.append(url)
            except (ConfigParser.NoOptionError):
                pass
            
        return urls 
    
    @property
    def config(self):
        configDir = locateDataDirectory('groupserver.GSFeedParser.config')
        fname = os.path.join(configDir, self.configId+'.ini')
        c = ConfigParser.ConfigParser()
        try:
            c.read(fname)
        except:
            log.error("Could not find config file %s" % fname)
            
        return c

class GSFeedContentProvider(object):
    """GroupServer Feed Content Provider
      
    """
    implements(IGSFeedContentProvider)
    adapts(Interface, IDefaultBrowserLayer, Interface)

    # We want a really simple cache for templates, because there aren't
    #  many of them
    cookedTemplates = SimpleCache("GSFeedContentProvider.cookedTemplates")
    atomTemplate = 'browser/templates/atom.pt'
      
    def __init__(self, context, request, view):
        self.__parent = view
        self.__updated = False
        self.context = context
        self.request = request
        self.view = view
        self.feed_config = GSFeedConfigReader(context, request)
        
    def update(self):
        self.siteInfo = Products.GSContent.view.GSSiteInfo(self.context)
        self.groupInfo = createObject('groupserver.GroupInfo',
                                      self.context)

        self.groupName = self.groupInfo.get_name()
        self.groupId = self.groupInfo.get_id()
        self.siteId = self.siteInfo.get_id()
        self.user = self.request.AUTHENTICATED_USER
        
        self.__updated = True
          
    def render(self):  
        if not self.__updated:
            raise UpdateNotCalled
        
        retval = ''
        
        feed_urls = self.feed_config.urls
        feeds = []
        for url in feed_urls:
            fname = md5.new(url).hexdigest()
            try:
                dataDir = locateDataDirectory(
                            'groupserver.GSFeedParser.data')
                v = pickle.load(file(os.path.join(dataDir, fname)))
                feeds.append(v)
            except:
                pass
        
        pageTemplate = self.cookedTemplates.get(self.atomTemplate)
              
        if not pageTemplate:
            pageTemplate = PageTemplateFile(self.atomTemplate)
            self.cookedTemplates.add(self.atomTemplate, pageTemplate)
    
        for feed in feeds:
            for entry in feed.entries:
                if entry.has_key('content'):
                    if isinstance(entry.content[0], unicode):
                        content = entry.content
                    else:
                        content = entry.content[0]
                else:
                    content = entry.summary
                      
                if isinstance(content, dict):
                    content = content.value
                      
                retval += pageTemplate(title=entry.title,
                                       date=entry.updated,
                                       content=content)
              
        return retval
          
    #########################################
    # Non standard methods below this point #
    #########################################

provideAdapter(GSFeedContentProvider, provides=IContentProvider,
  name="groupserver.DisplayFeed")