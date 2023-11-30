from django.urls import path
from .views import web_scrape

urlpatterns = [
    path('web_scrape/', web_scrape, name='web_scrape'),
]
