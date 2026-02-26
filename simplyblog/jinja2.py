import re

from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils.translation import get_language
from jinja2 import Environment


def demoji(s):
    RE_EMOJI = re.compile(
        "([\U00002600-\U000027bf])|([\U0001f300-\U0001f64f])|([\U0001f680-\U0001f6ff])"
    )
    return RE_EMOJI.sub(r"", s)


class JinjaEnvironment(Environment):
    def __init__(self, **kwargs):
        super(JinjaEnvironment, self).__init__(**kwargs)
        self.globals["messages"] = messages.get_messages
        self.globals["settings"] = settings
        self.globals["url"] = reverse
        self.globals["static"] = staticfiles_storage.url
        self.globals["demoji"] = demoji
        self.globals["get_language"] = get_language
