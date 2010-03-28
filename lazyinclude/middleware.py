import urllib
import re

from django.db import transaction
from django.core.cache import cache
from django.conf import settings
from django import template
from django.template.context import RequestContext
from django.utils import importlib

# TODO: improve key generation, this may only work for simple keys
# django's get_cache_key is out: no GET parameters and returns
# None if there is no key. Not very useful.
def _get_cache_key(request, prefix=''):
    cache_key = urllib.quote(request.path.encode("utf-8"))
    if request.GET:
        cache_key += "."+"".join(["%s:%s" % (k,v) for k,v in request.GET.items()])
    return prefix+cache_key

cache_key_module = getattr(settings, "GET_CACHE_KEY_MODULE", None)
if cache_key_module is not None:
    get_cache_key = importlib.import_module(cache_key_module).get_cache_key
else:
    get_cache_key = _get_cache_key

LAZYINCLUDE = re.compile('(\{% ?lazyinclude ?"([a-z/_]+\.html)" ?%\})')

class LazyIncludeMiddleware(object):
    """
    Check if caching should be done,
    tries to get the view result from cache
    if not in cache, gets the view result from the view
    checks if view result should be cached
    caches view result
    replaces any lazyinclude tags with their appropriate content
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != 'GET' or \
                any(map(request.path.endswith,getattr(settings, "DONT_CACHE_SUFFIXES", ()))) or \
                any(map(request.path.startswith,getattr(settings, "DONT_CACHE_URLS", ()))):
            return None
        
        cache_key = get_cache_key(request)
        from_cache = True
        response = cache.get(cache_key, None)
        if response is None:
            from_cache = False
            response = view_func(request, *view_args, **view_kwargs)
        if any(map(response['content-type'].startswith,getattr(settings, "CACHED_TYPES", ("text/html",)))):
            if not from_cache and response.status_code == 200:
                self.set_cache(cache_key, response, settings.CACHE_TIMEOUT)
            matches = LAZYINCLUDE.findall(response.content)
            for match in matches:
                include_snippet = self.render_template(match[1], request)
                response.content = response.content.decode("utf8").replace(match[0], include_snippet)
        return response
        
    def render_template(self, name, request):
        t = template.loader.get_template(name)
        return t.render(RequestContext(request))

    @transaction.commit_on_success
    def set_cache(self,cache_key, response, timeout):
        try:
            cache.set(cache_key, response, timeout)
        except Exception:
            # if db cache backend: most likely an 
            # OperationalError, because to packet size too big
            pass
