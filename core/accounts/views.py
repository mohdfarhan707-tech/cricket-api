from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _user_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": bool(user.is_staff),
        "is_superuser": bool(user.is_superuser),
    }


class IsStaffUser(BasePermission):
    """JWT-authenticated Django staff (or superuser)."""

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and (getattr(u, "is_staff", False) or getattr(u, "is_superuser", False))
        )


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        user = ser.save()
        tokens = _tokens_for_user(user)
        return Response(
            {
                **tokens,
                "user": _user_payload(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ident = ser.validated_data["identifier"].strip()
        password = ser.validated_data["password"]
        user = User.objects.filter(
            Q(email__iexact=ident) | Q(username__iexact=ident)
        ).first()
        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Invalid email/username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        tokens = _tokens_for_user(user)
        return Response(
            {
                **tokens,
                "user": _user_payload(user),
            }
        )


class AdminSummaryAPI(APIView):
    """Dashboard stats for staff (requires Bearer JWT from /api/auth/login/)."""

    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        from live.models import LiveMatch
        from matches.models import Match, Series

        return Response(
            {
                "users_total": User.objects.count(),
                "series_total": Series.objects.count(),
                "matches_total": Match.objects.count(),
                "live_match_rows": LiveMatch.objects.count(),
                "staff_email": request.user.email or "",
                "staff_username": request.user.username,
            }
        )
