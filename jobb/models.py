from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import reverse

User = get_user_model()

class Leverandorer(models.Model):
    name = models.CharField(max_length=64, blank=True)
    """Model definition for Leverandorer."""

    # TODO: Define fields here

    class Meta:
        """Meta definition for Leverandorer."""

        verbose_name = 'Leverandor'
        verbose_name_plural = 'Leverandorer'

    def __str__(self):
        """Unicode representation of Leverandorer."""
        return self.name


class Matriell(models.Model):
    """Model definition for Matriell."""
    el_nr = models.IntegerField(unique=True, blank=True, null=True,)
    tittel = models.CharField(max_length=64, unique=True, blank=True)
    info = models.CharField(max_length=256, blank=True)
    leverandor = models.ForeignKey(
        Leverandorer, on_delete=models.CASCADE, blank=True, null=True)
    image = models.ImageField(
        upload_to='matriell_image', default='default/matriell.png')
    # TODO: Define fields here

    class Meta:
        """Meta definition for Matriell."""

        verbose_name = 'Matriell'
        verbose_name_plural = 'Matriell'

    def __str__(self):
        """Unicode representation of Matriell."""
        return self.tittel

    def get_absolute_url(self):
        return reverse('matriell-detail', kwargs={'pk': self.pk})



class JobbMatriell(models.Model):
    """Model definition for Matriell."""
    matriell = models.ForeignKey(Matriell, on_delete=models.CASCADE)
    antall = models.IntegerField(default=1)
    jobb = models.ForeignKey('Jobber', on_delete=models.CASCADE)
    transf = models.BooleanField(default=False)

    # TODO: Define fields here

    class Meta:
        """Meta definition for Matriell."""

        verbose_name = 'JobbMatriell'
        verbose_name_plural = 'JobbMatriell'

    def __str__(self):
        """Unicode representation of Matriell."""
        return self.matriell.tittel


class Jobber(models.Model):
    """Model definition for Jobber."""
    ordre_nr = models.PositiveSmallIntegerField(primary_key=True)
    tittel = models.CharField(max_length=64, unique=True, blank=True)
    adresse = models.CharField(max_length=256, blank=True)
    telefon_nr = models.CharField(max_length=64, blank=True)
    beskrivelse = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    ferdig = models.BooleanField(default=False)
    matriell = models.ManyToManyField(JobbMatriell, blank=True)
    profile_picture = models.ImageField(
        upload_to='jobb_profile_image', default='default/jobb_profile.png')

    # TODO: Define fields here
    # Koble til timer og matriell

    class Meta:
        """Meta definition for Jobber."""

        verbose_name = 'Jobb'
        verbose_name_plural = 'Jobber'

    def __str__(self):
        """Unicode representation of Jobber."""
        return self.tittel


def get_jobb_image_filename(instance, filename):
    jobb_id = instance.jobb.pk
    return "post_images/%s" % (jobb_id/filename)


class JobbImage(models.Model):
    """Model definition for Jobb_images."""
    jobb = models.ForeignKey(Jobber, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='jobbimages',
                              verbose_name='Image')
    # TODO: Define fields here

    class Meta:
        """Meta definition for JobbImage."""

        verbose_name = 'JobbImage'
        verbose_name_plural = 'JobbImages'

    def __str__(self):
        """Unicode representation of JobbImage."""
        return self.jobb.tittel

