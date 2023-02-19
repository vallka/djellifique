import hashlib
import re
from google.cloud import translate_v2 as translate

from django.db import models

# Create your models here.
class Usage(models.Model):
    created_dt = models.DateTimeField("Created Date/Time", auto_now_add=True, null=True)
    chars = models.IntegerField("Chars",default=1)
    lang = models.CharField("Language",max_length=5)
    cached = models.BooleanField("Cached",default=False)

    class Meta:
        ordering = ['-id']

class GTransCache(models.Model):
    hash = models.CharField("Hash",max_length=100,primary_key=True)
    lang = models.CharField("Language",max_length=5,default='en')
    source = models.TextField("Text",default='')


class GTranslator:
    @staticmethod
    def translate(texts,target_languages,source_language):
        translate_client = translate.Client()

        translated_texts = {}
        for target_language in target_languages:
            chars = 0
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
        return translated_texts
