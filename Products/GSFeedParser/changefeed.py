# coding=utf-8
import ConfigParser, os
import ThreadLock

from zope.formlib import form
from zope.component import createObject
from Products.Five.formlib.formbase import PageForm
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from interfaces import IGSChangeWebFeed
from Products.XWFCore.XWFUtils import locateDataDirectory

import logging
log = logging.getLogger('GSFeedParser') #@UndefinedVariable


CONFIGPATH = locateDataDirectory('groupserver.GSFeedParser.config')

_thread_lock = ThreadLock.allocate_lock()

class GSChangeWebFeedSiteForm(PageForm):
    label = u'Change Web Feed'
    pageTemplateFileName = 'browser/templates/changefeedsite.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSChangeWebFeed, render_context=False)
      
    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.statusStart = u'Web feed for '\
          u'<a class="site" href="%s">%s</a>'%\
          (self.siteInfo.url, self.siteInfo.name)

        if not(request.form.has_key('form.feedUri')):
            request.form['form.feedUri'] = self.get_feed_uri()

    @form.action(label=u'Change', failure='handle_change_action_failure')
    def handle_change(self, action, data):
        assert self.context
        assert self.form_fields
        
        if data.get('feedUri', ''):
            self.set_feed_uri(data['feedUri'])
            self.status = u'%s is set to '\
              u'<a href="%s"><code>%s</code></a>.' % \
              (self.statusStart, data['feedUri'], data['feedUri'])
        else:
            self.clear_feed_uri()
            self.status = u'%s has been switched off.' % self.statusStart
            
        
        assert self.status
        assert type(self.status) == unicode

    def handle_change_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

    def get_feed_uri(self):
        assert hasattr(self, 'configFileName')
        config = ConfigParser.ConfigParser()
        config.read(self.configFileName)
        
        retval = ''
        if config.has_section('Home'):
            retval = config.get('Home', 'url')
        return retval
        
    def set_feed_uri(self, uri):
        m = u'Setting web feed URI for %s to %s' % \
          (self.configFileName, uri)
        log.info(m)

        config = ConfigParser.ConfigParser()
        config.read(self.configFileName)
        
        if not(config.has_section('Home')):
            config.add_section('Home')
        
        config.set('Home', 'name', 
          u'Feed displayed on the homepage')
        config.set('Home', 'url', uri)
        
        # avoid internal race conditions on write without using
        # file handle tricks
        try:
            _thread_lock.acquire()
            config.write(open(self.configFileName, 'w'))
        finally:
            _thread_lock.release()

    def clear_feed_uri(self):
        m = u'Clearing web feed URI for %s' % self.configFileName
        log.info(m)

        config = ConfigParser.ConfigParser()
        config.read(self.configFileName)
        
        if config.has_section('Home'):
            config.remove_section('Home')
        
        # avoid internal race conditions on write without using
        # file handle tricks
        try:
            _thread_lock.acquire()
            config.write(open(self.configFileName, 'w'))
        finally:
            _thread_lock.release()
        
    @property
    def configFileName(self):
        groupServerId = self.context.site_root().getId()
        fn = '%'.join((groupServerId, self.siteInfo.id, '')) + '.ini'
        siteConfigFile = os.path.join(CONFIGPATH, fn)
        return siteConfigFile

class GSChangeWebFeedGroupForm(GSChangeWebFeedSiteForm):
    pageTemplateFileName = 'browser/templates/changefeedgroup.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    def __init__(self, context, request):
        # --=mpj17=-- Trick for young players: if the groupInfo is
        #   not set early then Badness Happens.
        self.groupInfo = createObject('groupserver.GroupInfo', 
                                      context)
        GSChangeWebFeedSiteForm.__init__(self, context, request)
        self.statusStart = u'Web feed for '\
          u'<a class="group" href="%s">%s</a> is set to '%\
          (self.groupInfo.url, self.groupInfo.name)
        
    @property
    def configFileName(self):
        groupServerId = self.context.site_root().getId()
        p = (groupServerId, self.siteInfo.id, self.groupInfo.id)
        fn = '%'.join(p) + '.ini'
        groupConfigFile = os.path.join(CONFIGPATH, fn)
        return groupConfigFile

