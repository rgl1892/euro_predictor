"""
WSGI config for euro_predictor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'euro_predictor.settings')
os.environ['MEMCACHIER_USERNAME'] = 'C03897'
os.environ['MEMCACHIER_PASSWORD'] = '384CACB51DE2BC52B204D9F70BF57BBE'
os.environ['MEMCACHIER_SERVERS'] = 'mc3.c1.eu-central-1.ec2.memcachier.com:11211'

application = get_wsgi_application()
