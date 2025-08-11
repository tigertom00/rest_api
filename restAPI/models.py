from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
import os


# Users
class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        # Set username to the part before '@' if not provided
        if not extra_fields.get('username'):
            extra_fields['username'] = email.split('@')[0]
        # Set display_name to username.capitalize() if not provided
        if not extra_fields.get('display_name'):
            extra_fields['display_name'] = extra_fields['username'].capitalize()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class UserEmail(models.Model):
    user = models.ForeignKey('CustomUser', related_name='emails', on_delete=models.CASCADE)
    email = models.EmailField()
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email

class UserPhone(models.Model):
    user = models.ForeignKey('CustomUser', related_name='phones', on_delete=models.CASCADE)
    phone_nr = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_nr

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_image', default='default/profile.png')
    clerk_profile_image_url = models.URLField(blank=True, null=True)
    dark_mode = models.BooleanField(default=False)
    clerk_id = models.CharField(max_length=255, blank=True, null=True) #Getting clerk ID
    has_image = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    clerk_updated_at = models.DateTimeField(auto_now=True)



    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    


    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
            if len(self.username) < 4:
                self.username = self.username + os.urandom(2).hex()[:8]
        if not self.display_name and self.username:
            self.display_name = self.username.capitalize()
        elif self.display_name:
            self.display_name = self.display_name.capitalize()
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.email
    
