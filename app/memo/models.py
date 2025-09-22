from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class Leverandorer(models.Model):
    name = models.CharField(max_length=64, blank=True)
    manufacturer_code = models.CharField(max_length=30, blank=True, null=True)
    url = models.URLField(validators=[URLValidator()], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leverandor'
        verbose_name_plural = 'Leverandorer'

    def __str__(self):
        return self.name


class Matriell(models.Model):
    el_nr = models.CharField(max_length=32, unique=True, blank=True, null=True)
    tittel = models.CharField(max_length=255, blank=True)
    info = models.CharField(max_length=256, blank=True)
    leverandor = models.ForeignKey(
        Leverandorer, on_delete=models.CASCADE, blank=True, null=True
    )
    image = models.ImageField(
        upload_to='matriell_image', default='default/matriell.png', blank=True, null=True
    )
    favorites = models.BooleanField(default=False)

    # New fields from Norwegian electrical database
    ean_number = models.CharField(max_length=32, blank=True, null=True)
    article_number = models.CharField(max_length=32, blank=True, null=True)
    order_number = models.CharField(max_length=100, blank=True, null=True)
    type_designation = models.CharField(max_length=255, blank=True, null=True)
    norwegian_description = models.CharField(max_length=255, blank=True, null=True)
    english_description = models.CharField(max_length=255, blank=True, null=True)
    german_description = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=10, blank=True, null=True)
    datasheet_url = models.CharField(max_length=200, blank=True, null=True)
    list_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_factor = models.CharField(max_length=4, blank=True, null=True)
    vat = models.CharField(max_length=5, blank=True, null=True)
    weight = models.CharField(max_length=8, blank=True, null=True)
    unit_per_package = models.CharField(max_length=5, blank=True, null=True)
    height = models.CharField(max_length=20, blank=True, null=True)
    width = models.CharField(max_length=20, blank=True, null=True)
    depth = models.CharField(max_length=20, blank=True, null=True)
    approved = models.BooleanField(default=False)
    discontinued = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Matriell'
        verbose_name_plural = 'Matriell'

    def clean(self):
        if self.el_nr and Matriell.objects.filter(el_nr=self.el_nr).exclude(pk=self.pk).exists():
            raise ValidationError({'el_nr': 'Dette elektronummer finnes allerede.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tittel


class Jobber(models.Model):
    ordre_nr = models.PositiveSmallIntegerField(primary_key=True)
    tittel = models.CharField(max_length=64, unique=True, blank=True)
    adresse = models.CharField(max_length=256, blank=True)
    telefon_nr = models.CharField(max_length=64, blank=True)
    beskrivelse = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    ferdig = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to='jobb_profile_image', default='default/jobb_profile.png', blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jobb'
        verbose_name_plural = 'Jobber'

    @property
    def total_hours(self):
        return sum(timeliste.timer or 0 for timeliste in self.timeliste_set.all())

    def __str__(self):
        return self.tittel


class JobbMatriell(models.Model):
    matriell = models.ForeignKey(Matriell, on_delete=models.CASCADE)
    antall = models.IntegerField(default=1)
    jobb = models.ForeignKey(Jobber, on_delete=models.CASCADE, related_name="jobbmatriell")
    transf = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'JobbMatriell'
        verbose_name_plural = 'JobbMatriell'

    def __str__(self):
        return f"{self.antall}x {self.matriell.tittel} for {self.jobb.tittel}"

class JobberImage(models.Model):
    jobb = models.ForeignKey(
        "Jobber", on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="jobb_images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.jobb.tittel}"


class JobberFile(models.Model):
    jobb = models.ForeignKey(
        "Jobber", on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to="jobb_files/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.jobb.tittel}"
    
class Timeliste(models.Model):
    """Model definition for Timeliste."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    jobb = models.ForeignKey(Jobber, on_delete=models.CASCADE)
    beskrivelse = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dato = models.DateField(null=True, blank=True)
    timer = models.SmallIntegerField(null=True)

    # TODO: Define fields here

    class Meta:
        """Meta definition for Timeliste."""

        verbose_name = 'timeliste'
        verbose_name_plural = 'timelister'

    def __str__(self):
        """Unicode representation of Timeliste."""
        return f"Timeliste for {self.jobb.tittel}"