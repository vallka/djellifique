from django.shortcuts import render
from django.views import generic
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin



import os
from llama_index import (
    StorageContext, load_index_from_storage
)


def Bot(q):

    storage_context = StorageContext.from_defaults(persist_dir=os.path.join(settings.MEDIA_ROOT,"blog_store"))
    # load index
    index = load_index_from_storage(storage_context)

    query_engine = index.as_query_engine()
    response = query_engine.query(q)
    return response


# Create your views here.
class PageView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'chatbot/chatbot.html'

@api_view(['POST'])
def chatbot(request):
    question = request.data['question']
    print (question)
    answer = Bot(question)
    #print(answer,answer.source_nodes)
    
    #answer = f"Answer to {question}"
    return Response({'answer': str(answer)})