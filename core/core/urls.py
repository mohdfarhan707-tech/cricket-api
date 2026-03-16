"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from matches.views import MatchDashboardAPI, MatchScorecardAPI
from live.views import LiveMatchesAPI, LiveMatchScorecardAPI, LiveResultsAPI
from news.views import NewsAPI

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/matches/', MatchDashboardAPI.as_view()),
    path('api/matches/<str:match_id>/scorecard/', MatchScorecardAPI.as_view()),
    path('api/live-matches/', LiveMatchesAPI.as_view()),
    path('api/live-matches/<str:match_id>/scorecard/', LiveMatchScorecardAPI.as_view()),
    path('api/live-results/', LiveResultsAPI.as_view()),
    path('api/news/', NewsAPI.as_view()),
]
