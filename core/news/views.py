from rest_framework.views import APIView
from rest_framework.response import Response

from .models import NewsItem
from .serializers import NewsItemSerializer


class NewsAPI(APIView):
    def get(self, request):
        qs = NewsItem.objects.order_by("-published_at", "-id")[:50]
        serializer = NewsItemSerializer(qs, many=True)
        return Response(serializer.data)

