from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib
import re
from google.cloud import translate_v2 as translate
from .models import *


translate_client = translate.Client()

@csrf_exempt
def translate(request):
    if request.method == 'POST':
        # Parse the JSON input
        data = json.loads(request.body)
        q = data.get('q')
        target_language = data.get('target')

        if type(q) is list:
            texts = q
        else:
            texts = [q]

        chars = 0
        # Translate the texts
        translated_texts = []
        for text in texts:
            text = text.replace('\n',' ').replace('\r',' ').strip()
            text = re.sub(r'\s+',' ',text)

            h = hashlib.sha1(text.encode()).hexdigest()

            try:
                cached = GTransCache.objects.get(hash=h)
            except GTransCache.DoesNotExist:
                cached = GTransCache(hash=h,source=text)
                cached.save()

            try:
                result = GTransCacheLang.objects.get(lang=target_language,source=cached)
                result = result.target
                was_in_cache = True
            except GTransCacheLang.DoesNotExist:
                result = translate_client.translate(text, target_language=target_language,format_='html',source_language='en')
                result=result['translatedText']
                cache_lang = GTransCacheLang(lang=target_language,source=cached,target=result)
                cache_lang.save()
                was_in_cache = False

            translated_texts.append(result)
            chars += len(text)

        u = Usage(chars=chars,lang=target_language,cached=was_in_cache)
        u.save()

        # Return the translated texts in the response
        return HttpResponse(json.dumps({'translated_texts': translated_texts}), content_type='application/json')
    else:
        return HttpResponse('Error: Only POST requests are accepted')