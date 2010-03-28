import unittest
from django.conf import settings
from django.test import Client
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django import template
from django.core.cache import cache

from middleware import LazyIncludeMiddleware, _get_cache_key
from templatetags.lazyinclude_tags import lazyinclude

class RequestFactory(Client):
    """
    Taken from here: http://www.djangosnippets.org/snippets/963/
    ------
    Class that lets you create mock Request objects for use in testing.
    
    Usage:
    
    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})
    
    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client
    
    Once you have a request object you can pass it to any view function, 
    just as if that view had been hooked up using a URLconf.
    
    """
    def request(self, **request):
        """
        Similar to parent class, but returns the request object as soon as it
        has created it.
        """
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)


class LazyIncludeTest(unittest.TestCase):
    html = """
        {% load lazyinclude_tags %}
        <html>...
        {{ result_of_expensive_database_hit }}
        {% lazyinclude "_login.html" %}
        {{ output_of_user_input }}
        ...</html>
    """
    login_html = """2nd template rendering"""
    
    def setUp(self):
        self.middleware = LazyIncludeMiddleware()
        # need to patch render_template because RequestContext (context processors) are not available
        self.middleware.render_template = self.render_template
        self.rf = RequestFactory()
        self.template = template.Template(self.html)
        self.login_template = template.Template(self.login_html)
        
    def sample_view(self, request, *args, **kwargs):
        c = template.Context({"result_of_expensive_database_hit": "42 (took some time)", 
            "output_of_user_input": """{% lazyinclude evil.html %}{% lazyinclude "evil.html" %}"""})
        return HttpResponse(self.template.render(c))
        
    def render_template(self, name, request):
        self.assertFalse("evil" in name)
        return self.login_template.render(template.Context({}))

    def testLazyInclude(self):
        # post requests result in none
        post_request = self.rf.post('/hello/', {"foo": "bar"})
        self.assertTrue(self.middleware.process_view(post_request, lambda x: HttpResponse(), (), {}) is None)
        
        get_request = self.rf.get('/hello/')
        self.assertTrue(cache.get(_get_cache_key(get_request), None) is None)
        response = self.middleware.process_view(get_request, self.sample_view, (), {})
        cached_response = cache.get(_get_cache_key(get_request), None)
        view_response = self.sample_view(get_request)
        self.assertTrue(cached_response is not None)
        self.assertFalse(self.login_html in cached_response.content)
        self.assertTrue(self.login_html in response.content)
        self.assertEqual(view_response.content, cached_response.content)
