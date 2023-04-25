import re
from django.http import JsonResponse
from django.utils import timezone
from django.views import generic
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

import logging
logger = logging.getLogger(__name__)

from .models import *
from gtranslator.models import *
from newsletter.models import *


class ListView(generic.ListView):
    model = Post
    paginate_by = 10
    
    def get_queryset(self):
        
        posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,)
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
        
        self.q = self.request.GET.get('q')

        #sql = Post.objects.filter(blog_start_dt__lte="'"+str(timezone.now())+"'",blog=True,).query
        sql = Post.objects.filter(blog=True,).query
        sql = re.sub('ORDER BY.*$','',str(sql))

        #posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,title__contains=q)

        # sql = "select * from blog_post where match(title,text) against (%s in boolean mode) and blog=1 and blog_start_dt<=%s"
        sql += "and match(title,text) against (%s in boolean mode) and blog_start_dt<=now()"
        print(sql)


        posts = Post.objects.raw(sql,[self.q])
        self.len = len(posts)
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
        return context        


class HomeView(generic.ListView):
    model = Post
    paginate_by = 20
    template_name = "blog/post_home.html"

    
    def get_queryset(self):
        
        posts = Post.objects.filter(blog_start_dt__lte=timezone.now(),blog=True,).order_by('-blog_start_dt')
        cat_slug = self.kwargs.get('slug')
        self.request.session['category'] = cat_slug

        if cat_slug:
            self.home = False
            cat = Category.objects.get(slug=cat_slug)
            self.cat = cat
            posts = posts.filter(category=cat)
            return posts
        else:
            self.home = True
            self.cat = None
            cat_ex = Category.objects.filter(category__startswith='_')
            posts = posts.exclude(category__in=cat_ex).order_by('-blog_start_dt')[:4]

            self.shown = []
            for p in posts:
                print (p.id)
                self.shown.append(p.id)

            return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['post'] = context['post_list'] and context['post_list'][0]
        context['categories'] = Category.objects.all().order_by('id')

        page = int(self.request.GET.get('page',1))


        if self.home:
            context['breadcrumb'] = 'Home'
            context['post_list2'] = []
            cats = ['news-announcements','health-safety','corporate-company-news','education','new-products','popular-this-month']
            for i,cat_slug in enumerate(cats):
                cat = Category.objects.get(slug=cat_slug)
                context['post_list2'].append({
                        'name':cat.category,
                        'slug':cat.slug,
                        'posts':Post.objects.filter(blog_start_dt__lte=timezone.now(),
                        blog=True,
                        category=cat).exclude(id__in=self.shown).order_by('-blog_start_dt')[:2]})
        else:
            context['breadcrumb'] = self.cat.category

        context['page_title'] = context['breadcrumb']
        context['product_carousel'] = self.getBlogProducts()
        context['product_carousel2'] = self.getBlogProducts('2')

        return context        

    def getBlogProducts(self,pos=''):
        post = Post.objects.get(slug='_products_carousel'+pos)

        post.look_up_gellifique_product_carousel()

        pp = post.text.split('!')

        pp = ['!' + p.strip() for p in pp if p]
        post.text = '\n-----\n'.join(pp)

        #print(post.text)
        
        text = '<div>' + re.sub('<hr />','</div>\n<div>',post.formatted_markdown) + '</div>'
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
        lang = self.kwargs.get('lang')

        if not lang or lang == 'en':
            post.lang = lang
            return post

        #post_lang = get_object_or_404(PostLang, post=post, lang_iso_code=lang)
        try:
            post_lang = PostLang.objects.get(post=post, lang_iso_code=lang)
        except PostLang.DoesNotExist:
            post.lang = lang
            return post

        if post_lang.title: post.title = post_lang.title
        if post_lang.email_subject: post.email_subject = post_lang.email_subject
        if post_lang.text: post.text = post_lang.text

        post.lang = lang

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = re.sub(r'[^\x00-\x7F]',' ', context['post'].title)
        context['categories'] = Category.objects.all().order_by('id')

        this_dt = context['post'].blog_start_dt

        if this_dt:
            cat_slug = self.request.session.get('category')
            cat = None
            if cat_slug:
                cat = Category.objects.get(slug=cat_slug)
            
                next = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,blog_start_dt__gt=this_dt,category=cat
                ).order_by('blog_start_dt')[:1]

                prev = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,blog_start_dt__lt=this_dt,category=cat
                ).order_by('-blog_start_dt')[:1]

            else:
                next = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,blog_start_dt__gt=this_dt,
                ).order_by('blog_start_dt')[:1]

                prev = Post.objects.filter(
                    blog_start_dt__lte=timezone.now(),blog=True,blog_start_dt__lt=this_dt,
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
        lang = self.kwargs.get('lang')

        if not lang or lang == 'en':
            post.lang = lang
            return post

        post_lang = get_object_or_404(PostLang, post=post, lang_iso_code=lang)

        if post_lang.title: post.title = post_lang.title
        if post_lang.email_subject: post.email_subject = post_lang.email_subject
        if post_lang.text: post.text = post_lang.text

        post.text = re.sub(r'(https://www\.gellifique\.co\.uk/)(en)/',f"\g<1>{lang}/",post.text)
        post.text = re.sub(r'(https://www\.gellifique\.eu/)(en)/',f"\g<1>{lang}/",post.text)

        post.lang = lang

        return post

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

@require_POST
def translate(request,slug):

    print('translate:',slug)
    logger.info("translate:%s",slug)

    post = Post.objects.get(slug=slug)

    langs = ['es','fr','de','it','ro','pl','pt','uk']

    text = post.formatted_markdown
    text = text.replace('<h3>','<h3 [')
    text = text.replace('</h3>','] /h3>')

    result = GTranslator.translate( [post.title,post.email_subject,text], langs, 'en' )
    print(result)

    for lang in langs:
        text = result[lang][2]
        text = text.replace('<h3 [','<h3>',)
        text = text.replace('] /h3>','</h3>',)

        try:
            postlang = PostLang.objects.get(post=post,lang_iso_code=lang)
            postlang.title = result[lang][0]
            postlang.email_subject = result[lang][1]
            postlang.text = text
            postlang.save()

        except PostLang.DoesNotExist:   
            postlang = PostLang(post=post,lang_iso_code=lang)
            postlang.title = result[lang][0]
            postlang.email_subject = result[lang][1]
            postlang.text = text
            postlang.save()



    logger.info(result)

    logger.error("translate_result:%s",post.slug)


    return JsonResponse({'result':'ok'})    
