from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request):
    # Static index page for now.
    return render_to_response('ed_news/index.html',
                              {},
                              context_instance = RequestContext(request))
