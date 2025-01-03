import re
import os
import json
from django.http import JsonResponse,HttpResponseRedirect
from django.utils import timezone
from django.views import generic
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.translation import get_language
from django.contrib.sitemaps import Sitemap

from icecream import ic


import logging
logger = logging.getLogger(__name__)

from .models import *
from gtranslator.models import *
from newsletter.models import *

class ListView(generic.ListView):
    model = Post
    paginate_by = 10
    
    def get_queryset(self):
        
        posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,draft=False)
        cat_slug = self.kwargs.get('slug')
        if cat_slug:
            cat = Category.objects.get(slug=cat_slug)
            print (cat)
            posts = posts.filter(category=cat)
        else:
            cat_ex = Category.objects.filter(category__startswith='_')
            posts = posts.exclude(category__in=cat_ex)

        self.request.session['category'] = cat_slug

        return posts.order_by('-blog_start_dt')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['post'] = context['post_list'] and context['post_list'][0]
        context['categories'] = Category.objects.all().order_by('id')

        page = int(self.request.GET.get('page',1))

        n = 0
        for p in context['post_list']:
            if n>0 or page>1:
                #print(p.text)
                pics = re.finditer(r'\!\[\]\(',p.text)

                pos = [pic.start() for pic in pics]

                print(p.slug,pos)

                if len(pos)>1 and pos[0]<100:
                    p.text = p.text[0:pos[1]]
                    p.read_more = True
                
                elif len(pos)>0 and pos[0]>=100:
                    p.text = p.text[0:pos[0]]
                    p.read_more = True

                else:
                    crs = re.finditer(r'\n',p.text)    
                    pos = [cr.start() for cr in crs]
                    if len(pos)>3:
                        p.text = p.text[0:pos[3]]
                        p.read_more = True

            n += 1

        if context['post']:
            context['breadcrumb'] = re.sub(r'[^\x00-\x7F]',' ', context['post'].title)
            context['page_title'] = context['breadcrumb']
        return context        

class SearchView(generic.ListView):
    model = Post
    paginate_by = 50
    template_name = "blog/post_search.html"
    
    def get_queryset(self):
        host = self.request.META['HTTP_HOST']
        if '127.0.0.1' in host or 'gellifique.eu' in host:
            self.domain = Post.Domains.EU
        else:
            self.domain = Post.Domains.CO_UK

        self.q = self.request.GET.get('q')

        #sql = Post.objects.filter(blog_start_dt__lte="'"+str(timezone.now())+"'",blog=True,).query
        sql = Post.objects.filter(blog=True,draft=False,domain=self.domain).query
        sql = re.sub('ORDER BY.*$','',str(sql))

        #posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,title__contains=q)

        # sql = "select * from blog_post where match(title,text) against (%s in boolean mode) and blog=1 and blog_start_dt<=%s"
        sql += "and match(title,text) against (%s in boolean mode) and blog_start_dt<=now()"
        print(sql)


        posts = Post.objects.raw(sql,[self.q])
        self.len = len(posts)
        for p in posts:
            p.translated() #in place
        return posts

        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['post'] = context['post_list'] and context['post_list'][0]
        context['categories'] = Category.objects.all().order_by('id')

        page = int(self.request.GET.get('page',1))
        #q = self.request.GET.get('q')
        context['q'] = self.q

        context['breadcrumb'] = f'Search: {self.q} ({self.len})' 
        context['page_title'] = context['breadcrumb']
        context['current_domain'] = self.domain
        context['canonical_url'] = 'https://' + self.request.META['HTTP_HOST'].replace('blog.','www.') + self.request.get_full_path()
        context['page_image'] = context['post'].first_image
        context['page_description'] = context['post'].first_p
        return context        


class HomeView(generic.ListView):
    model = Post
    paginate_by = 20
    template_name = "blog/post_home.html"

    
    def get_queryset(self):

        host = self.request.META['HTTP_HOST']
        if '127.0.0.1' in host or 'gellifique.eu' in host:
            self.domain = Post.Domains.EU
        else:
            self.domain = Post.Domains.CO_UK
        
        posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,draft=False,domain=self.domain).order_by('-blog_start_dt')
        cat_slug = self.kwargs.get('slug')
        self.request.session['category'] = cat_slug

        if cat_slug:
            self.home = False
            cat = Category.objects.get(slug=cat_slug)
            self.cat = cat
            posts = posts.filter(category=cat)
            [p.translated() for p in posts]
            return posts
        else:
            self.home = True
            self.cat = None
            cat_ex = Category.objects.filter(category__startswith='_')
            posts = posts.exclude(category__in=cat_ex).order_by('-blog_start_dt')[:6]

            self.shown = []
            for p in posts:
                p.translated() #in place
                self.shown.append(p.id)

            return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['post'] = context['post_list'] and context['post_list'][0]
        context['categories'] = Category.objects.all().order_by('id')

        ic(self.request.get_full_path())

        if self.home:
            context['breadcrumb'] = 'Home'
            context['post_list2'] = []
            cats = ['news-announcements','health-safety','corporate-company-news','education','new-products','popular-this-month']
            for i,cat_slug in enumerate(cats):
                cat = Category.objects.get(slug=cat_slug).translate()
                posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),
                            blog=True,draft=False,
                            domain=self.domain,
                            category=cat).exclude(id__in=self.shown).order_by('-blog_start_dt')[:3]

                [p.translated() for p in posts]
                
                context['post_list2'].append({
                        'name':cat.category,
                        'slug':cat.slug,
                        'posts':posts})
        else:
            context['breadcrumb'] = self.cat.category

        context['page_title'] = context['breadcrumb']
        context['product_carousel'] = self.getBlogProducts()
        context['product_carousel2'] = self.getBlogProducts('2')
        context['current_domain'] = self.domain
        context['canonical_url'] = 'https://' + self.request.META['HTTP_HOST'].replace('blog.','www.') + self.request.get_full_path()
        context['page_image'] = context['post'].first_image
        context['page_description'] = context['post'].first_p

        return context        

    def getBlogProducts(self,pos=''):
        post = Post.objects.get(slug='_products_carousel'+pos)
        #text = '<div>' + re.sub('<hr />','</div>\n<div>',post.formatted_markdown) + '</div>'
        text = post.text
        text = re.sub('^.*\n\n===CACHED-HTML===\n','',text,flags=re.S)

        return text




    def getBlogProductsPresta(self):
        id_cat = 2
        db = 'presta'

        sql = """
            SELECT pl.id_product,pl.name FROM ps17_category_product cp 
            LEFT  JOIN ps17_product_shop ps ON cp.id_product=ps.id_product AND ps.id_shop=1 
            LEFT  JOIN ps17_product_lang pl ON cp.id_product=pl.id_product AND pl.id_lang=1 AND pl.id_shop=1
            WHERE id_category=%s AND ps.active=1 ORDER BY cp.position
        """

        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_cat])
            pp = cursor.fetchall()

            print (pp)


class PostView(generic.DetailView):
    model = Post

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, slug=self.kwargs['slug'])

        return post.translated()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context['breadcrumb'] = re.sub(r'[^\x00-\x7F]',' ', context['post'].title)
        context['breadcrumb'] = context['post'].title
        context['categories'] = Category.objects.all().order_by('id')

        host = self.request.META['HTTP_HOST']
        if '127.0.0.1' in host or 'gellifique.eu' in host:
            self.domain = Post.Domains.EU
        else:
            self.domain = Post.Domains.CO_UK

        context['current_domain'] = self.domain
        context['canonical_url'] = 'https://' + self.request.META['HTTP_HOST'].replace('blog.','www.') + self.request.get_full_path()
        context['page_title'] = context['breadcrumb']

        context['page_image'] = context['post'].first_image
        context['page_description'] = context['post'].first_p

        this_dt = context['post'].blog_start_dt

        if this_dt:
            cat_slug = self.request.session.get('category')
            cat = None
            if cat_slug:
                cat = Category.objects.get(slug=cat_slug)
            
                next = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,draft=False,blog_start_dt__gt=this_dt,category=cat
                ).order_by('blog_start_dt')[:1]

                prev = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,draft=False,blog_start_dt__lt=this_dt,category=cat
                ).order_by('-blog_start_dt')[:1]

            else:
                next = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,draft=False,blog_start_dt__gt=this_dt,
                ).order_by('blog_start_dt')[:1]

                prev = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,draft=False,blog_start_dt__lt=this_dt,
                ).order_by('-blog_start_dt')[:1]

            if len(next): 
                context['next'] = next[0].slug
            if len(prev): 
                context['prev'] = prev[0].slug

        context['post'].text = context['post'].text.replace('<referral_url>','')
        context['post'].text = context['post'].text.replace('<firstname>','')
        context['post'].text = context['post'].text.replace('<!-- Hi Firstname -->','')

        return context        

class NewsletterView(generic.DetailView):
    model = Post
    template_name = "blog/newsletter_detail.html"

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, slug=self.kwargs['slug'])
        return post.translated()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trustpilot'] = NewsShot.get_trustpilot()
        
        if context['post'].domain==Post.Domains.EU:
            context['www_gellifique'] = 'www.gellifique.eu'
        else:
            context['www_gellifique'] = 'www.gellifique.co.uk'

        #firstname = 'Margarita'
        #referral_url = 'https://www.gellifique.co.uk/?rid=1064'

        #context['post'].text = context['post'].text.replace('<referral_url>',referral_url)
        #context['post'].text = context['post'].text.replace('<firstname>',firstname)
        #context['post'].text = context['post'].text.replace('<!-- Hi Firstname -->',f"Hi {firstname},")

        return context

class MakePdfView(generic.DetailView):
    model = Post
    template_name = "blog/makepdf_detail.html"

    def get(self, request, *args, **kwargs):
        # Get the object for the detail view
        object = self.get_object()

        if isinstance(object, str):
            return HttpResponseRedirect(object)

        return super().get(request, *args, **kwargs)



    def get_object(self, queryset=None):
        post = get_object_or_404(Post, slug=self.kwargs['slug'])
        lang = self.kwargs.get('lang')
        page = int(self.request.GET.get('page',0))
        build = int(self.request.GET.get('build',0))

        post.translated()

        if not lang or lang == 'en':
            pages = post.text.split('-----')
        else:
            pages = post.text.split('<hr />')

        if page:
            post.text = pages[page-1]
        else:
            post.text += '<hr><hr>'

            for i in range(1,len(pages)+1):
                post.text += f' <a target="blank" href="{self.request.build_absolute_uri()}?page={i}&build=1" >pdf-{i}</a> '

        if build and page:
            import pdfkit

            url = self.request.build_absolute_uri().replace('build=1','build=0')

            config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF)
            pdfkit.from_url (url,os.path.join(settings.MEDIA_ROOT,'generated-pdf',post.slug+f'-{page}.pdf'),configuration=config)

            #return HttpResponseRedirect(os.path.join(settings.MEDIA_URL,'generated-pdf',post.slug+f'-{page}.pdf'))
            return (settings.MEDIA_URL + 'generated-pdf/' + post.slug+f'-{page}.pdf')
            #return HttpResponseRedirect(settings.MEDIA_URL + 'generated-pdf/' + post.slug+f'-{page}.pdf')

        return post



@require_POST
def translate(request,slug, target_language=None):

    post = Post.objects.get(slug=slug)
    r = post.gpt_translate(target_language)

    return JsonResponse(r)    

@require_POST
def punctuation(request):

    text = request.POST['text']
    ic('punctuation',text)

    prompt = f"""Check and correct punctuation only in the following markdown/html text.
Only check text. Don't touch URL links and other html attributes. Be careful not to delete line breaks and keep all markdown formatting.
Keep markdown/html format for text field in resulting JSON. 
Produce output in JSON format like this:

    'text': '...corrected text in markdown/html...',
    'your_comments': '... briefly list all your corrections ...'

Input text below:    

{text}
"""

    data = {
        'model': 'gpt-3.5-turbo-1106',
        #'model': 'gpt-4-1106-preview',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0,
        'response_format': { 'type': 'json_object' }
    }

    api_key = os.getenv('OPENAI_API_KEY')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    responseobj = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
    
    ic(responseobj.status_code)
    
    response = responseobj.text
    ic(response)
    response = json.loads(responseobj.text)
    print(f'DONE=============================')


    correction = json.loads(response['choices'][0]['message']['content'])
    your_comments = correction['your_comments']

    ic(correction)
    text = correction['text']

    r = {'result':'ok','text':text, 'usage':response['usage']['total_tokens'], 'comments': your_comments} 

    return JsonResponse(r)    

class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    site = None
    i18n = True

    def get_urls(self, page=1, site=None, protocol=None):
        #ic('BlogPostSitemap.get_urls',site)
        self.site = site

        return super().get_urls(page, site, protocol)

    def items(self):
        # Assuming you have a method to fetch episodes
        #ic('BlogPostSitemap.items',self,self.site.name)
        return Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,domain=Post.Domains.EU if '.eu' in self.site.name else Post.Domains.CO_UK)

    def lastmod(self, obj):
        # Assuming you have a date field for last modification
        return obj.updated_dt
    
    def get_domain(self, site=None):
        domain = super().get_domain(site)
        return domain.replace('blog.','www.')

class CategoryPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    site = None
    i18n = True

    def get_urls(self, page=1, site=None, protocol=None):
        #ic('CategoryPostSitemap.get_urls',site)
        self.site = site

        return super().get_urls(page, site, protocol)

    def items(self):
        # Assuming you have a method to fetch episodes
        #ic('CategoryPostSitemap.items',self,self.site.name)
        return Category.objects.exclude(category__startswith='_')

    def get_domain(self, site=None):
        domain = super().get_domain(site)
        return domain.replace('blog.','www.')
