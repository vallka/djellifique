import re
from this import d
import requests

from bs4 import BeautifulSoup

from django.db import models
from django.utils.text import slugify
#from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


# Create your models here.
class Category(models.Model):
    class Meta:
        ordering = ['slug']

    category = models.CharField(_("Category"), blank=True, max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), unique=True, max_length=100, blank=True, null=False)
    is_default = models.BooleanField(_("Default Category"),default=False)

    def __str__(self):
        return str(self.slug) + ' -- ' + str(self.category)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category)
            
        super().save(*args, **kwargs)

class Post(models.Model):
    class Meta:
        ordering = ['-id']

    title = models.CharField(_("Title"), max_length=100, unique=False)
    slug = models.SlugField(_("Slug"), unique=True, max_length=100, blank=True, null=False)

    blog = models.BooleanField(_("Publish to blog"),default=False)
    blog_start_dt = models.DateTimeField(_("Published"), blank=True, null=True)
    email = models.BooleanField(_("Send as newsletter"),default=False)
    email_subject = models.CharField(_("Subject"), max_length=100, blank=True, null=False, default='')
    email_send_dt = models.DateTimeField(_("Sent"), blank=True, null=True)

    class EmailStatus(models.IntegerChoices):
        NONE = 0
        SENDING = 1
        SENT = 2

    email_status = models.IntegerField(default=EmailStatus.NONE,choices=EmailStatus.choices)

    class Domains(models.IntegerChoices):
        CO_UK = 1
        EU = 2

    domain = models.IntegerField(default=Domains.CO_UK,choices=Domains.choices)

    category = models.ManyToManyField(Category, )

    title_color = models.CharField(_("Title Color"),max_length=20, blank=True, null=False, default='#232323')
    title_bgcolor = models.CharField(_("Title Bg Color"),max_length=20, blank=True, null=False, default='#eeeeee')

    text = MarkdownxField(_("Text"), blank=True, null=False)

    created_dt = models.DateTimeField(_("Created Date/Time"), auto_now_add=True, null=True)
    updated_dt = models.DateTimeField(_("Updated Date/Time"), auto_now=True, null=True)

    description  = models.TextField(_("Meta Description"), blank=True, null=False, default='')
    keywords  = models.TextField(_("Meta Keywords"), blank=True, null=False, default='')
    json_ld  = models.TextField(_("script ld+json"), blank=True, null=False, default='')


    @property
    def formatted_markdown(self):
        text = re.sub('~~([^~]+)~~',r'<s>\1</s>',self.text) # not in standard extensions
        return markdownify(text)

    @property
    def plain_text(self):
        text = re.sub('~~([^~]+)~~',r'<s>\1</s>',self.text) # not in standard extensions
        md = markdownify(text)

        md = re.sub('<a[^>]+?>','',md)
        md = re.sub(r'</a>','',md)
        md = re.sub('<img[^>]+?>','',md)
        return md
        #return '<p>'.join(BeautifulSoup(md,features="html.parser").findAll(text=True))
        #return '<p>' + ''.join(BeautifulSoup(md,features="html.parser").findAll(text=True)) + '</p>'

    @property
    def first_image(self):
        img = re.search(r'\!\[\]\(([^)]+)\)',self.text)
        if img and img.group(1):
            return img.group(1)
        else:
            return None

    def __str__(self):
        return str(self.id) + ':'+ str(self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(self.title)

            try:
                Post.objects.get(slug=slug)
                for i in range(1,1000):
                    try:
                        Post.objects.get(slug=slug+str(i))
                        continue
                    except Post.DoesNotExist:
                        slug = slug+str(i)
                        break

            except Post.DoesNotExist:
                None

            self.slug = slug

        self.look_up_gellifique_product()
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return '/blog/' + str(self.slug)        

    def look_up_gellifique_product(self):
        # [](https://www.gellifique.co.uk/en/pro-limited-edition/-periwinkle-hema-free(1342).html)

        print ('look_up_gellifique_product')
        #print (self.text)

        #product_re = r"(\r?\n<<<<\r?\n)(https:\/\/www.gellifique.co.uk\/.+?\.html)\r?\n([^\n]*\r?\n)?"
        product_re = r"(\r?\n((<<<<)|(>>>>))\r?\n?)(https:\/\/www\.gellifique\.[couke.]+/.+?\.html)((\r?\n)|($))"

        prods = re.findall(product_re,self.text)
        
        if prods:
            print (prods)

            for prod in prods:
                print (prod[0],prod[4])
                prod_html = requests.get(prod[4].replace('\\','')) # '\\' started to be inserted for unknown reason by frontend js
                if prod_html.status_code == 200:
                    print ('soup::')
                    prod_html = prod_html.text
                    prod_href = prod[4]

                    soup = BeautifulSoup(prod_html, 'html.parser')
                    prod_name = soup.find('h1',attrs={'itemprop':'name','class':'h1'})
                    prod_descr = soup.find('div',attrs={'class':'product-description'})
                    prod_descr_pp = prod_descr.find_all('p')

                    if prod_descr_pp[0].text!='PRODUCT DESCRIPTION':
                        prod_descr = prod_descr_pp[0].text.strip()
                    else:
                        prod_descr = prod_descr_pp[1].text.strip()

                    print(prod_descr)

                    prod_price = prod_name.parent.find(attrs={'itemprop':'price'})
                    prod_img = prod_name.parent.parent.find('img',attrs={'itemprop':'image'})

                    old_price = prod_name.parent.find('span',attrs={'class':'regular-price'})
                    discount = prod_name.parent.find('span',attrs={'class':'discount'})

                    if old_price and discount:
                        discount_p = f"<p><del>{old_price.text}</del> <span class='discount'>{discount.text}</span></p>\n"
                    else:
                        discount_p = ''

                    if '<' in prod[0]:
                        product = f"""
<!-- {prod[0].strip()}{prod_href}
--><table class="product"><tr><td>	
<a href="{prod_href}"><img src="{prod_img['src']}"></a>
</td><td>	
<h3>{prod_name.text} - {prod_price.text}</h3>
{discount_p}<p>
{prod_descr}
</p>
<h4><a href="{prod_href}">BUY NOW</a></h4>
</td></tr></table>
"""
                    else:
                        product = f"""
<!-- {prod[0].strip()}{prod_href}
--><table class="product"><tr><td>	
<h3>{prod_name.text} - {prod_price.text}</h3>
{discount_p}<p>
{prod_descr}
</p>
<h4><a href="{prod_href}">BUY NOW</a></h4>
</td><td>	
<a href="{prod_href}"><img src="{prod_img['src']}"></a>
</td></tr></table>
"""

                    self.text = re.sub(product_re,product,self.text,1)



    def look_up_gellifique_product_carousel(self):
        # [](https://www.gellifique.co.uk/en/pro-limited-edition/-periwinkle-hema-free(1342).html)

        #print ('look_up_gellifique_product')

        product_re = r"(\[\])\((https:\/\/gellifique.eu\/.+?\.html)\)"
        product_re = r"(\[\])\((https:\/\/www.gellifique.co.uk\/.+?\.html)\)"
        ##product_re = r"\((https:\/\/www.gellifique.co.uk\/.+\.html)\)"

        prods = re.findall(product_re,self.text)
        
        if prods:
            print (prods)

            for prod in prods:
                print (prod[1])
                prod_html = requests.get(prod[1].replace('\\','')) # '\\' started to be inserted for unknown reason by frontend js
                if prod_html.status_code == 200:
                    print ('soup::')
                    prod_html = prod_html.text

                    soup = BeautifulSoup(prod_html, 'html.parser')
                    prod_name = soup.find('h1',attrs={'itemprop':'name','class':'h1'})
                    prod_price = prod_name.parent.find(attrs={'itemprop':'price'})
                    prod_img = prod_name.parent.parent.find('img',attrs={'itemprop':'image'})

                    old_price = prod_name.parent.find('span',attrs={'class':'regular-price'})
                    discount = prod_name.parent.find('span',attrs={'class':'discount'})

                    if old_price and discount:
                        discount_p = f"<p><del>{old_price.text}</del> <span class='discount'>{discount.text}</span></p>"
                    else:
                        discount_p = ''

                    print (prod_img['src'])

                    self.text = re.sub(product_re,f"![]({prod_img['src']})\n####[{prod_name.text} - {prod_price.text}]({prod[1]})",self.text,1)

class PostLang(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    lang_iso_code = models.CharField(_("Language ISO Code"), max_length=5)
    title = models.CharField(_("Title"), max_length=100, default='')
    email_subject = models.CharField(_("Subject"), max_length=100, blank=True, null=False, default='')
    text = models.TextField(_("Text"), blank=True, null=False, default='')
    description = models.TextField(_("Meta Description"), blank=True, null=False, default='')
    keywords  = models.TextField(_("Meta Keywords"), blank=True, null=False, default='')
    json_ld  = models.TextField(_("script ld+json"), blank=True, null=False, default='')
    class Meta:
        unique_together = ('post', 'lang_iso_code')


class AllLanguages:
    # needs to match table content: ps17_lang
    langs = ['','','es','de','fr','pt','pl','ro','it','uk']

    @classmethod
    def getById(cls,id):
        return cls.langs[id]

        

