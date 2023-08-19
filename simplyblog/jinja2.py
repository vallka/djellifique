import re
from django.contrib import messages
from jinja2 import Environment
from django.conf import settings
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage

def demoji(s):
    return re.sub(r'[^\x00-\x7F]',' ', s)
    

class JinjaEnvironment(Environment):

    def __init__(self,**kwargs):
        super(JinjaEnvironment, self).__init__(**kwargs)
        self.globals['messages'] = messages.get_messages
        self.globals['settings'] = settings
        self.globals['url'] = reverse
        self.globals['static'] = staticfiles_storage.url
        self.globals['demoji'] = demoji
