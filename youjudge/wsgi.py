"""
WSGI config for YouJudge project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'youjudge.settings')

application = get_wsgi_application()
