import re
import os
import json
import requests

from bs4 import BeautifulSoup
from icecream import ic

from django.db import models
from django.utils.text import slugify
#from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from django.utils.translation import get_language

import logging
logger = logging.getLogger(__name__)

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

    def translate(self):
        lang = get_language()

        if not lang or lang == 'en':
            return self

        try:
            category_lang = CategoryLang.objects.get(category=self, lang_iso_code=lang)
        except CategoryLang.DoesNotExist:
            return self

        if category_lang.category_text: self.category = category_lang.category_text
        return self

class Post(models.Model):
    class Meta:
        ordering = ['-id']

    title = models.CharField(_("Title"), max_length=100, unique=False)
    slug = models.SlugField(_("Slug"), unique=True, max_length=100, blank=True, null=False)

    blog = models.BooleanField(_("Publish to blog"),default=False)
    blog_start_dt = models.DateTimeField(_("Published"), blank=True, null=True)
    email = models.BooleanField(_("Send as newsletter"),default=False)
    email_subject = models.CharField(_("Subject"), max_length=100, blank=True, null=False, default='')
    email_subsubject = models.CharField(_("Sub-Subject"), max_length=100, blank=True, null=False, default='')
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
        
        img = re.search(r'<img[^>]+src="(.*?)"',self.text)
        if img and img.group(1):
            return img.group(1)

        return None

    @property
    def first_p(self):
        text = re.sub('~~([^~]+)~~',r'<s>\1</s>',self.text) # not in standard extensions
        p = markdownify(text)
        
        p1 = ''
        n = 0
        while not p1 and p and n<=10:
            n += 1
            p = re.sub(r'^.*?<p>\s*','',p,flags=re.S)
            p1 = re.sub('</p>.*$','',p,flags=re.S)
            p1 = re.sub('<.*?>','',p1)
            p1 = p1.strip()
            if p1 and len(p1)>150: 
                return p1


        p2 = ''
        n = 0
        while not p2 and p and n<=10:
            n += 1
            p = re.sub(r'^.*?<p>\s*','',p,flags=re.S)
            p2 = re.sub('</p>.*$','',p,flags=re.S)
            p2 = re.sub('<.*?>','',p2)
            p2 = p2.strip()
            if p1 and p2: 
                return f'{p1}<br><br>{p2}'

        return p1 + ' ' + p2
    
    def translated(self):
        lang = get_language()

        if not lang or lang == 'en':
            self.lang = lang
            return self

        try:
            post_lang = PostLang.objects.get(post=self, lang_iso_code=lang)
        except PostLang.DoesNotExist:
            self.lang = lang
            return self

        if post_lang.title: self.title = post_lang.title
        if post_lang.email_subject: self.email_subject = post_lang.email_subject
        if post_lang.email_subsubject: self.email_subsubject = post_lang.email_subsubject
        if post_lang.text: self.text = post_lang.text
        if post_lang.description: self.description = post_lang.description
        if post_lang.keywords: self.keywords = post_lang.keywords
        if post_lang.json_ld: self.json_ld = post_lang.json_ld

        self.lang = lang

        self.text = re.sub(r'(https://www\.gellifique\.co\.uk/)(en)/',f"\g<1>{lang}/",self.text)
        self.text = re.sub(r'(https://www\.gellifique\.eu/)(en)/',f"\g<1>{lang}/",self.text)

        return self


    def gpt_translate(self, target_language=None):
        print('translate:',self.slug,target_language)
        logger.info("translate:%s",self.slug)

        if target_language:
            langs = [target_language]
        else:
            langs = ['es','fr','de','it','ro','pl','pt','uk']

        text = self.text

#        text = f'''<title>{self.title}</title>
#<subject>{self.email_subject}</subject>
#<subsubject>{self.email_subsubject}</subsubject>
#-----
#{text}
#'''
        text = json.dumps ({
            'title': self.title,
            'subject': self.email_subject,
            'subsubject': self.email_subsubject,
            'text': self.text
        })

        print(f'=============================>')
        ic(text)

        api_key = os.getenv('OPENAI_API_KEY')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }


        for lang in langs:
            prompt = f"""Translate the following blog post in JSON format into '{lang}'
Keep markdown/html format for text field. Don't translate product names, leave them in English.
Also replace '/en/' to '/{lang}/' in URLs: https://www.gellifique.co.uk/en/ should become https://www.gellifique.co.uk/{lang}/
Produce output in JSON format like this:

    'title': '...translated title...', 
    'subject': '...translated subject...',
    'subsubject': '...translated subsubject...',
    'text': '...translated text...',
    'your_comments': '... if you have any comments or questions, put here...'

Input JSON below:    
    
{text}
"""

            data = {
                #'model': 'gpt-3.5-turbo',
                'model': 'gpt-3.5-turbo-1106',
                'messages': [
                    {'role': 'system', 'content': 'You are a translator with a knowledge of beauty industry and manicure in particular.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0,
                'response_format': { 'type': 'json_object' }

            }

            print(f'> {lang}')
            responseobj = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
            
            ic(responseobj.status_code)
            
            response = responseobj.text
            response = json.loads(responseobj.text)
            print(f'DONE============================= {lang}')
            ic(response)

            translation = json.loads(response['choices'][0]['message']['content'])
            #ic(response['usage'])

            title = translation['title']
            subject = translation['subject']
            subsubject = translation['subsubject']

            translated_text = translation['text']
            your_comments = translation['your_comments']

            ic(title,subject,subsubject,translated_text)
            ic(your_comments)

            try:
                postlang = PostLang.objects.get(post=self,lang_iso_code=lang)
                postlang.title = title[:100]
                postlang.email_subject = subject[:100]
                postlang.text = translated_text
                postlang.email_subsubject = subsubject[:100]
                postlang.save()

            except PostLang.DoesNotExist:   
                postlang = PostLang(post=self,lang_iso_code=lang)
                postlang.title = title[:100]
                postlang.email_subject = subject[:100]
                postlang.text = translated_text
                postlang.email_subsubject = subsubject[:100]
                postlang.save()


        logger.error("translate_result:%s",self.slug)
        return {'result':'ok','usage':response['usage']['total_tokens']}    


    def __str__(self):
        return str(self.id) + ':'+ str(self.slug)

    def save(self, *args, **kwargs):
        if not self.email_subject:
            self.email_subject = self.title

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

        if self.slug=='_products_carousel' or self.slug=='_products_carousel2':
            self.look_up_gellifique_product_carousel()
        else:
            self.look_up_gellifique_product()
            
        super().save(*args, **kwargs)

        if self.domain==Post.Domains.EU:
            ic(AllLanguages.langs[2:])
            for lang in AllLanguages.langs[2:]:
                try:
                    postlang = PostLang.objects.get(post=self,lang_iso_code=lang)

                except PostLang.DoesNotExist:   
                    postlang = PostLang(post=self,lang_iso_code=lang)
                    ic(self.title)
                    postlang.title = self.title
                    postlang.save()

    def get_absolute_url(self):
        return reverse('blog:post', kwargs={'slug': self.slug})    

    def look_up_gellifique_product(self):
        # [](https://www.gellifique.co.uk/en/pro-limited-edition/-periwinkle-hema-free(1342).html)

        print ('look_up_gellifique_product')
        #print (self.text)

        #product_re = r"(\r?\n<<<<\r?\n)(https:\/\/www.gellifique.co.uk\/.+?\.html)\r?\n([^\n]*\r?\n)?"
        #product_re = r"^((<{2,30})|(>{2,30}))\r?\n?(https:\/\/www\.gellifique\.[couke.]+/.+?\.html)$"
        product_re = r"^\s*((<{2,30})|(>{2,30})|(<>))\s*(https:\/\/www\.gellifique\.[couke.]+/.+?\.html.*)\s*$"

        prods = re.findall(product_re,self.text,flags=re.M)
        
        if prods:
            print (prods)

            #return

            for prod in prods:
                prod_href = prod[4].replace('\\','').strip()  # '\\' started to be inserted for unknown reason by frontend js
                print (prod[0],f'|{prod_href}|')
                prod_html = requests.get(prod_href) 
                print(prod_html.status_code)
                if prod_html.status_code == 200:
                    prod_html = prod_html.text

                    soup = BeautifulSoup(prod_html, 'html.parser')
                    prod_name = soup.find('h1',attrs={'class':'h1'})
                    prod_descr = soup.find('div',attrs={'class':'product-description'})
                    prod_descr_pp = prod_descr.find_all('p')

                    if prod_descr_pp[0].text.strip().find('PRODUCT')>=0:
                        prod_descr = prod_descr_pp[1].text.strip()
                    else:
                        prod_descr = prod_descr_pp[0].text.strip()


                    prod_price = prod_name.parent.find(attrs={'class':'current-price'}).find('span')
                    prod_img = prod_name.parent.parent.find('img',attrs={'class':'js-qv-product-cover'})

                    old_price = prod_name.parent.find('span',attrs={'class':'regular-price'})
                    discount = prod_name.parent.find('span',attrs={'class':'discount'})

                    if old_price and discount:
                        discount_p = f"<p><del>{old_price.text}</del> <span class='discount'>{discount.text}</span></p>\n"
                    else:
                        discount_p = ''

                    print("**DESCR:",prod_descr,prod_price,prod_img)

                    if '<>' in prod[0]:
                        print('***<>')
                        product = f"""
<!-- {prod[0].strip()}{prod_href}
--><table class="product"><tr><td>	
<a href="{prod_href}"><img src="{prod_img['src']}"></a>
<h3>{prod_name.text} - {prod_price.text}</h3>
{discount_p}<p>
{prod_descr}
</p>
<h4><a href="{prod_href}">BUY NOW</a></h4>
</td></tr></table>
"""
                    elif '<<' in prod[0]:
                        print('***<<')
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
                        print('***>>')
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

                    print ("***PRODUCT:",product)

                    self.text = re.sub(product_re,product,self.text,1,flags=re.M)



    def look_up_gellifique_product_carousel(self):
        # [](https://www.gellifique.co.uk/en/pro-limited-edition/-periwinkle-hema-free(1342).html)

        #print ('look_up_gellifique_product')

        product_re = r"(\[\])\((https:\/\/gellifique.eu\/.+?\.html)\)"
        product_re = r"(\[\])\((https:\/\/www.gellifique.co.uk\/.+?\.html.*)\)"
        ##product_re = r"\((https:\/\/www.gellifique.co.uk\/.+\.html)\)"

        prods = re.findall(product_re,self.text)
        
        if prods:
            #print (prods)

            text = ''

            for prod in prods:
                #print (prod[1])
                prod_html = requests.get(prod[1].replace('\\','')) # '\\' started to be inserted for unknown reason by frontend js
                if prod_html.status_code == 200:
                    prod_html = prod_html.text

                    soup = BeautifulSoup(prod_html, 'html.parser')
                    prod_name = soup.find('h1',attrs={'class':'h1'})
                    prod_price = prod_name.parent.find(attrs={'class':'current-price'}).find('span')
                    prod_img = prod_name.parent.parent.find('img',attrs={'class':'js-qv-product-cover'})

                    old_price = prod_name.parent.find('span',attrs={'class':'regular-price'})
                    discount = prod_name.parent.find('span',attrs={'class':'discount'})

                    if old_price and discount:
                        discount_p = f"<p><del>{old_price.text}</del> <span class='discount'>{discount.text}</span></p>"
                    else:
                        discount_p = ''

                    #print (prod_img['src'])

                    text += f"![]({prod_img['src']})\n####[{prod_name.text} - {prod_price.text}]({prod[1]})\n" 
                
            orig_text = self.text

            orig_text = re.sub('===CACHED-HTML===.*$','',orig_text,flags=re.S).strip()

            self.text = text
            self.text = orig_text + "\n\n===CACHED-HTML===\n" + self.formatted_markdown
            self.text = self.text.replace('<p><img','<div><p><img')
            self.text = self.text.replace('</h4>','</h4></div>')



class PostLang(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    lang_iso_code = models.CharField(_("Language ISO Code"), max_length=5)
    title = models.CharField(_("Title"), max_length=100, default='')
    email_subject = models.CharField(_("Subject"), max_length=100, blank=True, null=False, default='')
    email_subsubject = models.CharField(_("Sub-Subject"), max_length=100, blank=True, null=False, default='')
    text = MarkdownxField(_("Text"), blank=True, null=False)
    description = models.TextField(_("Meta Description"), blank=True, null=False, default='')
    keywords  = models.TextField(_("Meta Keywords"), blank=True, null=False, default='')
    json_ld  = models.TextField(_("script ld+json"), blank=True, null=False, default='')

    @property
    def slug(self):
        return self.post.slug

    class Meta:
        unique_together = ('post', 'lang_iso_code')

class CategoryLang(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    lang_iso_code = models.CharField(_("Language ISO Code"), max_length=5)
    category_text = models.CharField(_("Category"), max_length=100, default='')

    def __str__(self):
        return self.lang_iso_code + ' ' + self.category_text



class AllLanguages:
    # needs to match table content: ps17_lang
    langs = ['','','es','de','fr','pt','pl','ro','it','uk']

    @classmethod
    def getById(cls,id):
        return cls.langs[id]

        

