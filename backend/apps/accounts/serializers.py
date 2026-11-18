from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    """Minimal representation of a user for mentions, comments, and lists."""
    avatar_url = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'full_name',
            'avatar_url',
            'is_private',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Complete user profile with engagement stats and editable fields."""
    avatar_url = serializers.ReadOnlyField()
    posts_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    follow_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'profile_picture',
            'avatar_url',
            'bio',
            'website',
            'location',
            'is_private',
            'is_email_verified',
            'posts_count',
            'followers_count',
            'following_count',
            'is_following',
            'follow_status',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'email',
            'username',
            'avatar_url',
            'is_email_verified',
            'posts_count',
            'followers_count',
            'following_count',
            'is_following',
            'follow_status',
            'date_joined',
        ]

    def get_posts_count(self, obj: User) -> int:
        return obj.posts_count

    def get_followers_count(self, obj: User) -> int:
        return obj.followers_count

    def get_following_count(self, obj: User) -> int:
        return obj.following_count

    def get_is_following(self, obj: User) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user == obj:
            return False
        return obj.follower_relations.filter(follower=request.user, is_pending=False).exists()

    def get_follow_status(self, obj: User) -> str:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 'none'
        if request.user.id == obj.id:
            return 'self'
        from apps.social.services import SocialService
        return SocialService.get_follow_status(request.user, obj)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Handles new user registration with strict validation."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'password',
            'password_confirm',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'full_name': {'required': True},
        }

    def validate_username(self, value: str) -> str:
        clean_username = value.strip().lower()
        if len(clean_username) < 3:
            raise serializers.ValidationError('Username must be at least 3 characters long.')
        if User.objects.filter(username__iexact=clean_username).exists():
            raise serializers.ValidationError('This username is already taken.')
        return clean_username

    def validate_email(self, value: str) -> str:
        clean_email = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=clean_email).exists():
            raise serializers.ValidationError('An account with this email address already exists.')
        return clean_email

    def validate(self, attrs: dict) -> dict:
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validates user login credentials using email or username."""
    identifier = serializers.CharField(
        required=True,
        help_text="User's email address or username."
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class ChangePasswordSerializer(serializers.Serializer):
    """Handles password updates for authenticated users."""
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs: dict) -> dict:
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({'new_password_confirm': 'New passwords do not match.'})
        if attrs.get('current_password') == attrs.get('new_password'):
            raise serializers.ValidationError({'new_password': 'New password cannot be identical to current password.'})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Accepts email address to initiate password reset flow."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates uidb64, reset token, and applies new password."""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs: dict) -> dict:
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({'new_password_confirm': 'New passwords do not match.'})
        return attrs
