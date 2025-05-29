from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

# Users
class CustomUserManager(UserManager):
    pass


class CustomUser(AbstractUser):
    objects = CustomUserManager()
    display_name = models.CharField(max_length=13)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_image', default='default/profile.png')
    dark_mode = models.BooleanField(default=False)


    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.username.capitalize()
        self.display_name = self.display_name.capitalize()
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.username
    
