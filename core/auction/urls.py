from django.urls import path

from .views import (
    AuctionBeginAPI,
    AuctionBidAPI,
    AuctionCreateAPI,
    AuctionPoolPreviewAPI,
    AuctionRestartAPI,
    AuctionResumeAPI,
    AuctionStateAPI,
    AuctionStopAPI,
)

urlpatterns = [
    path("auction/pool-preview/", AuctionPoolPreviewAPI.as_view()),
    path("auction/create/", AuctionCreateAPI.as_view()),
    path("auction/<uuid:session_id>/begin/", AuctionBeginAPI.as_view()),
    path("auction/<uuid:session_id>/state/", AuctionStateAPI.as_view()),
    path("auction/<uuid:session_id>/bid/", AuctionBidAPI.as_view()),
    path("auction/<uuid:session_id>/stop/", AuctionStopAPI.as_view()),
    path("auction/<uuid:session_id>/resume/", AuctionResumeAPI.as_view()),
    path("auction/<uuid:session_id>/restart/", AuctionRestartAPI.as_view()),
]
