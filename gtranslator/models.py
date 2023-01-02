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
    hash = models.CharField("Hash",max_length=100)
    source = models.TextField("Source")

class GTransCacheLang(models.Model):
    source = models.ForeignKey(GTransCache,on_delete=models.CASCADE)
    lang = models.CharField("Language",max_length=5)
    target = models.TextField("Target")

