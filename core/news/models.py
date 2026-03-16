from django.db import models


class NewsItem(models.Model):
    source = models.CharField(max_length=100, default="ESPNcricinfo")
    title = models.CharField(max_length=500)
    link = models.URLField(unique=True)
    summary = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    image_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.title

