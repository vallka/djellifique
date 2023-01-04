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


