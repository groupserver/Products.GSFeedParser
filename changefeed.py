# coding=utf-8

import ConfigParser, os

from zope.formlib import form
from zope.component import createObject
from Products.Five.formlib.formbase import PageForm
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from interfaces import IGSChangeWebFeed
from feedfetcher import CONFIGPATH

class GSChangeWebFeedSiteForm(PageForm):
    label = u'Change Web Feed'
    pageTemplateFileName = 'browser/templates/changefeedsite.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSChangeWebFeed)
      
    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.statusStart = u'Web feed for '\
          u'<a class="site" href="%s">%s</a> is set to '%\
          (self.siteInfo.url, self.siteInfo.name)

    @form.action(label=u'Change', failure='handle_change_action_failure')
    def handle_change(self, action, data):
        assert self.context
        assert self.form_fields
        
        self.set_feed_uri(data['feedUri'])
        
        self.status = u'<a href="%s"><code>%s</code></a>.' % \
          (self.statusStart, data['feedUri'], data['feedUri'])
        assert self.status
        assert type(self.status) == unicode

    def handle_change_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

    def set_feed_uri(self, uri):
        config = ConfigParser.ConfigParser()
        config.read(self.configFileName)
        
        if not(config.has_section('Home')):
            config.add_section('Home')
        
        config.set('Home', 'name', 
          u'Feed displayed on the homepage')
        config.set('Home', 'url', uri)
        
        config.write(open(self.configFileName, 'w'))
        
    @property
    def configFileName(self):
        groupServerId = self.context.site_root().getId()
        fn = '%'.join((groupServerId, self.siteInfo.id, '')) + '.ini'
        siteConfigFile = os.path.join(CONFIGPATH, fn)
        print siteConfigFile 
        return siteConfigFile

class GSChangeWebFeedGroupForm(GSChangeWebFeedSiteForm):
    pageTemplateFileName = 'browser/templates/changefeedgroup.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        self.statusStart = u'Web feed for '\
          u'<a class="group" href="%s">%s</a> is set to '%\
          (self.groupInfo.url, self.groupInfo.name)
        
    @property
    def configFileName(self):
        groupServerId = self.context.site_root().getId()
        p = (groupServerId, self.siteInfo.id, self.groupInfo.id)
        fn = '%'.join(p) + '.ini'
        groupConfigFile = os.path.join(CONFIGPATH, fn)
        print groupConfigFile
        return groupConfigFile

