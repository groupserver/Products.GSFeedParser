# coding=utf-8

import ConfigParser
from zope.formlib import form
from zope.component import createObject
from Products.Five.formlib.formbase import PageForm
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from interfaces import IGSChangeWebFeed

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
        self.status = u"stuff."
        assert self.status
        assert type(self.status) == unicode

    def handle_change_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

