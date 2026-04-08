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
from django.contrib.admin import AdminSite
from django.urls import path, include

# Clearer admin: branding + logical app order on the index (matches → live → auction → rankings → auth).
admin.site.site_header = "Cricket administration"
admin.site.site_title = "Cricket admin"
admin.site.index_title = "Overview"

_orig_get_app_list = AdminSite.get_app_list


def _get_app_list_ordered(self, request, app_label=None):
    app_list = _orig_get_app_list(self, request, app_label)
    priority = {
        "matches": 10,
        "live": 20,
        "auction": 30,
        "rankings": 40,
        "auth": 100,
    }
    app_list.sort(key=lambda a: (priority.get(a["app_label"], 50), a.get("name") or ""))
    return app_list


AdminSite.get_app_list = _get_app_list_ordered
from matches.views import MatchDashboardAPI, MatchScorecardAPI, TeamComparisonAPI, TeamLastNAPI, TeamHeadToHeadAPI, TeamFormAPI, MatchHighlightsAPI
from matches.views import BblSeriesStatsAPI
from live.views import LiveMatchesAPI, LiveMatchScorecardAPI, LiveResultsAPI
from news.views import NewsAPI
from rankings.views import RankingsAPI
from upcoming.views import UpcomingMatchesAPI, TeamSquadAPI, LeagueStandingsAPI

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/matches/', MatchDashboardAPI.as_view()),
    path('api/matches/<str:match_id>/scorecard/', MatchScorecardAPI.as_view()),
    path('api/matches/<str:match_id>/highlights/', MatchHighlightsAPI.as_view()),
    path('api/team-comparison/', TeamComparisonAPI.as_view()),
    path('api/team-lastn/', TeamLastNAPI.as_view()),
    path('api/head-to-head/', TeamHeadToHeadAPI.as_view()),
    path('api/team-form/', TeamFormAPI.as_view()),
    path('api/live-matches/', LiveMatchesAPI.as_view()),
    path('api/live-matches/<str:match_id>/scorecard/', LiveMatchScorecardAPI.as_view()),
    path('api/live-results/', LiveResultsAPI.as_view()),
    path('api/news/', NewsAPI.as_view()),
    path('api/rankings/<str:kind>/', RankingsAPI.as_view()),
    path('api/upcoming-matches/', UpcomingMatchesAPI.as_view()),
    path('api/league-standings/', LeagueStandingsAPI.as_view()),
    path('api/team-squad/', TeamSquadAPI.as_view()),
    path('api/bbl-stats/', BblSeriesStatsAPI.as_view()),
    path('api/', include('auction.urls')),
]
