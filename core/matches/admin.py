from django.contrib import admin
from .models import Series, Match

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('team_home', 'team_away', 'series', 'status')
    list_filter = ('series', 'status')
