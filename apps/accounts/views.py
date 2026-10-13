from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import UserSerializer, RegisterSerializer
from apps.audit.models import AuditEvent

class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({"csrfToken": token})

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            AuditEvent.objects.create(
                actor=user,
                action='USER_REGISTER',
                resource_type='User',
                resource_id=str(user.id),
                request_id=request.headers.get('X-Request-ID', '')
            )
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            AuditEvent.objects.create(
                actor=user,
                action='USER_LOGIN',
                resource_type='User',
                resource_id=str(user.id),
                request_id=request.headers.get('X-Request-ID', '')
            )
            return Response(UserSerializer(user).data)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        AuditEvent.objects.create(
            actor=user,
            action='USER_LOGOUT',
            resource_type='User',
            resource_id=str(user.id),
            request_id=request.headers.get('X-Request-ID', '')
        )
        logout(request)
        return Response({'message': 'Successfully logged out'})

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
