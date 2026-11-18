from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_.]+$',
    message='Usernames can only contain letters, numbers, underscores, and periods.'
)


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, username, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field is required.')
        if not username:
            raise ValueError('The Username field is required.')
        if not full_name:
            raise ValueError('The Full Name field is required.')

        email = self.normalize_email(email).lower()
        username = username.strip().lower()

        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(
            email=email,
            username=username,
            full_name=full_name.strip(),
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model for Circlo.
    Supports email authentication, unique usernames for social profiles,
    and profile information accessible directly or extended via signals.
    """
    email = models.EmailField(
        verbose_name='email address',
        unique=True,
        db_index=True,
        error_messages={'unique': 'An account with this email address already exists.'}
    )
    username = models.CharField(
        verbose_name='username',
        max_length=30,
        unique=True,
        db_index=True,
        validators=[username_validator],
        error_messages={'unique': 'This username is already taken.'}
    )
    full_name = models.CharField(
        verbose_name='full name',
        max_length=150
    )
    profile_picture = models.ImageField(
        verbose_name='profile picture',
        upload_to='profile_pictures/%Y/%m/',
        blank=True,
        null=True
    )
    bio = models.TextField(
        verbose_name='biography',
        max_length=500,
        blank=True
    )
    website = models.URLField(
        verbose_name='website',
        max_length=255,
        blank=True
    )
    location = models.CharField(
        verbose_name='location',
        max_length=120,
        blank=True
    )

    # Privacy and Verification settings
    is_private = models.BooleanField(
        verbose_name='private account',
        default=False,
        help_text='When enabled, only approved followers can see posts and stories.'
    )
    is_email_verified = models.BooleanField(
        verbose_name='email verified',
        default=False
    )

    # Account status & permissions
    is_active = models.BooleanField(
        verbose_name='active',
        default=True,
        help_text='Designates whether this user should be treated as active.'
    )
    is_staff = models.BooleanField(
        verbose_name='staff status',
        default=False,
        help_text='Designates whether the user can log into the admin site.'
    )
    date_joined = models.DateTimeField(
        verbose_name='date joined',
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        verbose_name='last updated',
        auto_now=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"@{self.username} ({self.email})"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email).lower()
        if self.username:
            self.username = self.username.strip().lower()

    @property
    def avatar_url(self):
        """Returns the profile picture URL or a fallback placeholder."""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-avatar.svg'

    @property
    def followers_count(self) -> int:
        """Returns approved followers count."""
        if hasattr(self, 'follower_relations'):
            return self.follower_relations.filter(is_pending=False).count()
        return 0

    @property
    def following_count(self) -> int:
        """Returns active following count."""
        if hasattr(self, 'following_relations'):
            return self.following_relations.filter(is_pending=False).count()
        return 0

    @property
    def posts_count(self) -> int:
        """Returns user authored posts count."""
        if hasattr(self, 'posts'):
            return self.posts.count()
        return 0
