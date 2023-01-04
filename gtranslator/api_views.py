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
    """Translate text from a source language to one or more target languages.

    The text and languages can be provided in a JSON object in the request body,
    with the following format:
    {
        "q": "text to translate",
        "source": "source language code (optional, default: 'en')",
        "target": ["target language code 1", "target language code 2", ...]
    }

    If the "q" field is an array, all the texts in the array will be translated.
    If the "target" field is not an array, it will be treated as a single-element array.

    The translation results are returned in a JSON object in the response body,
    with the following format:
    {
        "ok": true/false,
        "translated_texts": {
            "target_language_code_1": ["translated text 1", "translated text 2", ...],
            "target_language_code_2": ["translated text 1", "translated text 2", ...],
            ...
        }
    }

    If the request is not a POST request, or if an error occurs, the "ok" field
    will be set to false and an "Error" field will be included in the response,
    with a description of the error.

    Args:
        request (HttpRequest): Django HTTP request object.

    Returns:
        HttpResponse: Django HTTP response object.
    """

    if request.method == 'POST':
        # Parse the JSON input
        try:
            data = json.loads(request.body)
            q = data.get('q')
            source_language = data.get('source') or 'en'
            target_languages = data.get('target')

            if type(target_languages) is list:
                None
            else:
                target_languages = [target_languages]

            if type(q) is list:
                texts = q
            else:
                texts = [q]

            chars = 0

            translated_texts = {}
            for target_language in target_languages:
                # Translate the texts
                translated_texts[target_language] = []
                for text in texts:
                    text = text.replace('\n',' ').replace('\r',' ').strip()
                    text = re.sub(r'\s+',' ',text)

                    h = hashlib.sha1(text.encode()).hexdigest()
                    hs = f"{h}-{source_language}"
                    ht = f"{h}-{target_language}"

                    try:
                        cached = GTransCache.objects.get(hash=hs)
                    except GTransCache.DoesNotExist:
                        cached = GTransCache(hash=hs,source=text,lang=source_language)
                        cached.save()

                    try:
                        result = GTransCache.objects.get(hash=ht)
                        result = result.source
                        was_in_cache = True
                    except GTransCache.DoesNotExist:
                        result = translate_client.translate(text, target_language=target_language,format_='html',source_language='en')
                        result=result['translatedText']
                        cached = GTransCache(hash=ht,source=result,lang=target_language)
                        cached.save()
                        was_in_cache = False

                    translated_texts[target_language].append(result)
                    chars += len(text)

            u = Usage(chars=chars,lang=target_language,cached=was_in_cache)
            u.save()

            # Return the translated texts in the response
            return HttpResponse(json.dumps({'ok':True,'translated_texts': translated_texts}), content_type='application/json')
        except Exception as e:
            return HttpResponse(json.dumps({'ok':False,'Error': str(e)}), content_type='application/json')    


    else:
        return HttpResponse(json.dumps({'ok':False,'Error': 'Only POST requests are accepted'}), content_type='application/json')
