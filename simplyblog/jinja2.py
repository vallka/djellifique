import re
from django.contrib import messages
from jinja2 import Environment
from django.conf import settings
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.translation import get_language

def demoji(s):
    RE_EMOJI = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
    return RE_EMOJI.sub(r'', s)

    

class JinjaEnvironment(Environment):

    def __init__(self,**kwargs):
        super(JinjaEnvironment, self).__init__(**kwargs)
        self.globals['messages'] = messages.get_messages
        self.globals['settings'] = settings
        self.globals['url'] = reverse
        self.globals['static'] = staticfiles_storage.url
        self.globals['demoji'] = demoji
        self.globals['get_language'] = get_language
