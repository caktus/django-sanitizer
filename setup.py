#!/usr/bin/env python

from distutils.core import setup


setup(name="django-sanitizer",
      version="0.2",
      description="Django template filter application for sanitizing user submitted HTML",
      author="Calvin Spealman",
      url="http://github.com/caktus/django-sanitizer",
      packages=['sanitizer', 'sanitizer.templatetags'],
      )
