from django.conf.urls import patterns, include, url
from splunkdj.utility.views import render_template as render

urlpatterns = patterns('',
    url(r'^overview/$', render('SplunkforMobileDeviceForensics:overview.html'), name='overview'),
    # Phone Details
    url(r'^contacts/$', render('SplunkforMobileDeviceForensics:contacts.html'), name='contacts'),
    url(r'^calls/$', render('SplunkforMobileDeviceForensics:calls.html'), name='calls'),
    url(r'^sms/$', render('SplunkforMobileDeviceForensics:sms.html'), name='sms'),
    # Applications
    url(r'^browsinghabits/$', render('SplunkforMobileDeviceForensics:browsinghabits.html'), name='browsinghabits'),
    url(r'^skype/$', render('SplunkforMobileDeviceForensics:skype.html'), name='skype'),
    url(r'^applications/$', render('SplunkforMobileDeviceForensics:applications.html'), name='applications'),
    
    url(r'^timeline/$', render('SplunkforMobileDeviceForensics:timeline.html'), name='timeline')
)
