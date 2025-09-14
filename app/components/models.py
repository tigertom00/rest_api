from django.db import models
from django.core.validators import URLValidator

class Tag(models.Model):
    name_en = models.CharField(max_length=100)
    name_no = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name_en


class Llmproviders(models.Model):
    name = models.CharField(max_length=64, blank=True)
    url = models.URLField(validators=[URLValidator()], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    description_nb = models.TextField(blank=True)
    strengths_en = models.JSONField(default=list, blank=True)
    strengths_no = models.JSONField(default=list, blank=True)
    pricing = models.CharField(max_length=10, choices=[
        ('Free', 'Free'),
        ('Paid', 'Paid'),
    ], default='Free')
    pricing_nb = models.CharField(max_length=10, choices=[
        ('Gratis', 'Gratis'),
        ('Betalt', 'Betalt'),
    ], default='Gratis')
    icon = models.ImageField(upload_to='llmprovider_icons/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, related_name='llmproviders', blank=True)

    class Meta:
        verbose_name = 'Llmprovider'
        verbose_name_plural = 'Llmproviders'

    def __str__(self):
        return self.name