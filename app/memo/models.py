from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from restAPI.mixins import GeocodableMixin

User = get_user_model()


class ElektriskKategori(models.Model):
    blokknummer = models.CharField(
        max_length=2,
        unique=True,
        help_text="2-digit block number (e.g., '10', '11', '12')",
    )
    kategori = models.CharField(
        max_length=100, help_text="Category name (e.g., 'Kabler og ledninger')"
    )
    beskrivelse = models.TextField(help_text="Detailed description and examples")
    slug = models.SlugField(
        max_length=120, unique=True, help_text="URL-friendly version of category name"
    )
    etim_gruppe = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Related ETIM group code (e.g., 'EC000000')",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Elektrisk Kategori"
        verbose_name_plural = "Elektriske Kategorier"
        ordering = ["blokknummer"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.kategori)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.blokknummer} - {self.kategori}"


class Leverandorer(models.Model):
    name = models.CharField(
        max_length=100, unique=True, help_text="Company name (maps to 'navn' in JSON)"
    )
    telefon = models.CharField(
        max_length=50, blank=True, null=True, help_text="Phone number"
    )
    hjemmeside = models.URLField(blank=True, null=True, help_text="Website URL")
    addresse = models.CharField(
        max_length=200, blank=True, null=True, help_text="Address"
    )
    poststed = models.CharField(
        max_length=100, blank=True, null=True, help_text="City/postal place"
    )
    postnummer = models.CharField(
        max_length=20, blank=True, null=True, help_text="Postal code"
    )
    epost = models.EmailField(blank=True, null=True, help_text="Email address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leverandør"
        verbose_name_plural = "Leverandører"

    def __str__(self):
        return self.name


class Matriell(models.Model):
    # Core identification
    el_nr = models.CharField(max_length=32, unique=True)
    tittel = models.CharField(max_length=255)
    leverandor = models.ForeignKey(Leverandorer, on_delete=models.CASCADE)
    kategori = models.ForeignKey(
        ElektriskKategori, on_delete=models.CASCADE, null=True, blank=True
    )

    # Product details from EFO Basen JSON
    varemerke = models.CharField(
        max_length=100, blank=True, null=True, help_text="Brand/manufacturer"
    )
    info = models.TextField(blank=True, help_text="Technical description/ETIM info")
    varenummer = models.CharField(
        max_length=50, blank=True, null=True, help_text="Product number"
    )
    gtin_number = models.CharField(
        max_length=32, blank=True, null=True, help_text="GTIN/EAN code"
    )

    # Descriptions
    teknisk_beskrivelse = models.TextField(
        blank=True, null=True, help_text="Detailed technical description"
    )
    varebetegnelse = models.CharField(
        max_length=255, blank=True, null=True, help_text="Product designation"
    )

    # Dimensions (using DecimalField for precise measurements)
    hoyde = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Height in mm"
    )
    bredde = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Width in mm"
    )
    lengde = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Length/depth in mm",
    )
    vekt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Weight in grams",
    )

    # Documents and media
    bilder = models.JSONField(default=list, blank=True, help_text="Array of image URLs")
    produktblad = models.URLField(
        blank=True, null=True, help_text="Product datasheet URL"
    )
    produkt_url = models.URLField(
        blank=True, null=True, help_text="Manufacturer product page URL"
    )
    fdv = models.URLField(blank=True, null=True, help_text="FDV document URL")
    cpr_sertifikat = models.URLField(
        blank=True, null=True, help_text="CPR certificate URL"
    )
    miljoinformasjon = models.URLField(
        blank=True, null=True, help_text="Environmental information URL"
    )

    # Status
    approved = models.BooleanField(default=True)
    discontinued = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    favorites = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Matriell"
        verbose_name_plural = "Matriell"
        ordering = ["el_nr"]

    def clean(self):
        if (
            self.el_nr
            and Matriell.objects.filter(el_nr=self.el_nr).exclude(pk=self.pk).exists()
        ):
            raise ValidationError({"el_nr": "Dette elektronummer finnes allerede."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.el_nr} - {self.tittel}"


class Jobber(GeocodableMixin, models.Model):
    # Tell the mixin which field contains the address
    address_field = "adresse"
    ordre_nr = models.PositiveSmallIntegerField(primary_key=True)
    tittel = models.CharField(max_length=64, unique=True, blank=True)
    adresse = models.CharField(max_length=256, blank=True)
    telefon_nr = models.CharField(max_length=64, blank=True)
    beskrivelse = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    ferdig = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to="jobb_profile_image",
        default="default/jobb_profile.png",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Geocoding fields inherited from GeocodableMixin

    class Meta:
        verbose_name = "Jobb"
        verbose_name_plural = "Jobber"
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["ferdig", "latitude", "longitude"]),
        ]

    @property
    def total_hours(self):
        return sum(timeliste.timer or 0 for timeliste in self.timeliste_set.all())

    def __str__(self):
        return self.tittel


class JobbMatriell(models.Model):
    matriell = models.ForeignKey(Matriell, on_delete=models.CASCADE)
    antall = models.IntegerField(default=1)
    jobb = models.ForeignKey(
        Jobber, on_delete=models.CASCADE, related_name="jobbmatriell"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    transf = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "JobbMatriell"
        verbose_name_plural = "JobbMatriell"

    def __str__(self):
        return f"{self.antall}x {self.matriell.tittel} for {self.jobb.tittel}"


class JobberImage(models.Model):
    jobb = models.ForeignKey("Jobber", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="jobb_images/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.jobb.tittel}"


class JobberFile(models.Model):
    jobb = models.ForeignKey("Jobber", on_delete=models.CASCADE, related_name="files")
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

        verbose_name = "timeliste"
        verbose_name_plural = "timelister"

    def __str__(self):
        """Unicode representation of Timeliste."""
        return f"Timeliste for {self.jobb.tittel}"
