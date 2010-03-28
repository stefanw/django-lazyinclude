from distutils.core import setup

setup(
    name='django-lazyinclude',
    version='0.1.0',
    description='django-lazyinclude lets users annotate text fields of other models',
    author='Stefan Wehrmeyer',
    author_email='Stefan Wehrmeyer <mail@stefanwehrmeyer.com>',
    url='http://github.com/stefanw/django-lazyinclude',
    packages = ["lazyinclude", "lazyinclude.templatetags"],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)