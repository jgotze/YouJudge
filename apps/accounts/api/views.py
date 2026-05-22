from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, UserRegistrationSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from apps.accounts.models import EmailVerificationToken, PasswordResetToken
from apps.accounts.tasks import send_verification_email, send_password_reset_email

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own data
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create verification token
            token = EmailVerificationToken.objects.create(user=user)
            send_verification_email.delay(user.id, str(token.token))

            return Response({
                'message': 'Registration successful. Please check your email to verify your account.',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({'message': 'Password changed successfully.'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def password_reset_request(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
                token = PasswordResetToken.objects.create(user=user)
                send_password_reset_email.delay(user.id, str(token.token))
            except User.DoesNotExist:
                pass
            except Exception:
                return Response(
                    {'error': 'Failed to send reset email. Please try again later.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({'message': 'If an account exists with this email, a reset link will be sent.'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def password_reset_confirm(self, request):
        """Confirm password reset."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                reset_token = PasswordResetToken.objects.get(token=serializer.validated_data['token'])

                if not reset_token.is_valid():
                    return Response(
                        {'error': 'Invalid or expired reset token.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = reset_token.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()

                reset_token.used = True
                reset_token.save()

                return Response({'message': 'Password reset successfully.'})

            except PasswordResetToken.DoesNotExist:
                return Response(
                    {'error': 'Invalid reset token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
