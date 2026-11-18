"""
Development settings for Circlo social media application.
"""
from .base import *  # noqa: F403
import os
import sys

DEBUG = True

ALLOWED_HOSTS = ['*']

# Console Email Backend for local development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Detect if running under pytest or manage.py test
IS_TESTING = (
    'pytest' in sys.modules
    or any('test' in arg for arg in sys.argv)
    or os.environ.get('USE_SQLITE', 'False').lower() in ('true', '1')
)

if IS_TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
        }
    }
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'circlo-test-cache',
        }
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Disable WhiteNoise strict manifest requirements in local dev
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
