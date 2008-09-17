# coding=utf-8

import ConfigParser, os

from zope.formlib import form
from zope.component import createObject
from Products.Five.formlib.formbase import PageForm
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from interfaces import IGSChangeWebFeed
from feedfetcher import CONFIGPATH

class GSChangeWebFeedForm(PageForm):
    label = u'Change Web Feed'
    pageTemplateFileName = 'browser/templates/changefeed.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSChangeWebFeed)
      
    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.siteInfo = createObject('groupserver.SiteInfo', context)

    @form.action(label=u'Change', failure='handle_change_action_failure')
    def handle_change(self, action, data):
        assert self.context
        assert self.form_fields
        
        self.set_feed_uri(data['feedUri'])
        
        self.status = u'Web feed for <a href="%s">%s</a> set to '\
          u'<a href="%s"><code>%s</code></a>.' % \
          (self.siteInfo.url, self.siteInfo.name,
           data['feedUri'], data['feedUri'])
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
        
        if not(config.has_section('SiteHome')):
            config.add_section('SiteHome')
        
        config.set('SiteHome', 'name', 
          u'Feed displayed on the site homepage')
        config.set('SiteHome', 'url', uri)
        
        config.write(open(self.configFileName, 'w'))
        
    @property
    def configFileName(self):
        groupServerId = self.context.site_root().getId()
        fn = '%'.join((groupServerId, self.siteInfo.id, '')) + '.ini'
        siteConfigFile = os.path.join(CONFIGPATH, fn)
        print siteConfigFile 
        return siteConfigFile

