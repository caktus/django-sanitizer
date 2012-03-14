#!/usr/bin/env python

from distutils.core import setup


setup(name="django-sanitizer",
      version="0.4",
      description="Django template filter application for sanitizing user submitted HTML",
      author="Caktus Consulting Group",
      maintainer="Calvin Spealman",
      maintainer_email="calvin@caktusgroup.com",
      url="http://github.com/caktus/django-sanitizer",
      packages=['sanitizer', 'sanitizer.templatetags'],
      )
