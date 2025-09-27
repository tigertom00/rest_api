from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django_filters import rest_framework as filters

from .models import (
    ElektriskKategori,
    Jobber,
    JobbMatriell,
    Leverandorer,
    Matriell,
    Timeliste,
)

User = get_user_model()


class MatriellFilter(filters.FilterSet):
    # Text search fields
    search = filters.CharFilter(
        method="filter_search", help_text="Search across multiple fields"
    )

    # Exact match filters
    el_nr = filters.CharFilter(field_name="el_nr", lookup_expr="icontains")
    tittel = filters.CharFilter(field_name="tittel", lookup_expr="icontains")
    varemerke = filters.CharFilter(field_name="varemerke", lookup_expr="icontains")
    varenummer = filters.CharFilter(field_name="varenummer", lookup_expr="icontains")
    gtin_number = filters.CharFilter(field_name="gtin_number", lookup_expr="exact")

    # Foreign key filters
    kategori = filters.ModelChoiceFilter(
        field_name="kategori",
        queryset=ElektriskKategori.objects.all(),
        to_field_name="id",
        help_text="Filter by category ID",
    )
    kategori_blokknummer = filters.CharFilter(
        field_name="kategori__blokknummer",
        lookup_expr="exact",
        help_text='Filter by category block number (e.g., "10")',
    )
    kategori_name = filters.CharFilter(
        field_name="kategori__kategori",
        lookup_expr="icontains",
        help_text="Filter by category name",
    )

    leverandor = filters.ModelChoiceFilter(
        field_name="leverandor",
        queryset=Leverandorer.objects.all(),
        to_field_name="id",
        help_text="Filter by supplier ID",
    )
    leverandor_name = filters.CharFilter(
        field_name="leverandor__name",
        lookup_expr="icontains",
        help_text="Filter by supplier name",
    )

    # Boolean filters
    approved = filters.BooleanFilter(field_name="approved")
    discontinued = filters.BooleanFilter(field_name="discontinued")
    in_stock = filters.BooleanFilter(field_name="in_stock")
    favorites = filters.BooleanFilter(field_name="favorites")

    # Numeric range filters
    hoyde_min = filters.NumberFilter(
        field_name="hoyde", lookup_expr="gte", help_text="Minimum height in mm"
    )
    hoyde_max = filters.NumberFilter(
        field_name="hoyde", lookup_expr="lte", help_text="Maximum height in mm"
    )
    bredde_min = filters.NumberFilter(
        field_name="bredde", lookup_expr="gte", help_text="Minimum width in mm"
    )
    bredde_max = filters.NumberFilter(
        field_name="bredde", lookup_expr="lte", help_text="Maximum width in mm"
    )
    lengde_min = filters.NumberFilter(
        field_name="lengde", lookup_expr="gte", help_text="Minimum length in mm"
    )
    lengde_max = filters.NumberFilter(
        field_name="lengde", lookup_expr="lte", help_text="Maximum length in mm"
    )
    vekt_min = filters.NumberFilter(
        field_name="vekt", lookup_expr="gte", help_text="Minimum weight in grams"
    )
    vekt_max = filters.NumberFilter(
        field_name="vekt", lookup_expr="lte", help_text="Maximum weight in grams"
    )

    # Date range filters
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    updated_after = filters.DateTimeFilter(field_name="updated_at", lookup_expr="gte")
    updated_before = filters.DateTimeFilter(field_name="updated_at", lookup_expr="lte")

    # Ordering
    ordering = filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("el_nr", "el_nr"),
            ("tittel", "tittel"),
            ("varemerke", "varemerke"),
            ("hoyde", "hoyde"),
            ("bredde", "bredde"),
            ("lengde", "lengde"),
            ("vekt", "vekt"),
        ),
        field_labels={
            "created_at": "Creation Date",
            "updated_at": "Update Date",
            "el_nr": "El Number",
            "tittel": "Title",
            "varemerke": "Brand",
            "hoyde": "Height",
            "bredde": "Width",
            "lengde": "Length",
            "vekt": "Weight",
        },
        help_text='Order results by field. Use "-" for descending order (e.g., "-created_at")',
    )

    class Meta:
        model = Matriell
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        # Multi-field search across the most relevant text fields
        return queryset.filter(
            models.Q(el_nr__icontains=value)
            | models.Q(tittel__icontains=value)
            | models.Q(varemerke__icontains=value)
            | models.Q(info__icontains=value)
            | models.Q(teknisk_beskrivelse__icontains=value)
            | models.Q(varebetegnelse__icontains=value)
            | models.Q(varenummer__icontains=value)
            | models.Q(kategori__kategori__icontains=value)
            | models.Q(leverandor__name__icontains=value)
        ).distinct()


class ElektriskKategoriFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search", help_text="Search categories")
    blokknummer = filters.CharFilter(field_name="blokknummer", lookup_expr="exact")
    kategori = filters.CharFilter(field_name="kategori", lookup_expr="icontains")
    beskrivelse = filters.CharFilter(field_name="beskrivelse", lookup_expr="icontains")

    ordering = filters.OrderingFilter(
        fields=(
            ("blokknummer", "blokknummer"),
            ("kategori", "kategori"),
            ("created_at", "created_at"),
        ),
        help_text='Order by field. Use "-" for descending (e.g., "-blokknummer")',
    )

    class Meta:
        model = ElektriskKategori
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            models.Q(blokknummer__icontains=value)
            | models.Q(kategori__icontains=value)
            | models.Q(beskrivelse__icontains=value)
        ).distinct()


class LeverandorerFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search", help_text="Search suppliers")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    poststed = filters.CharFilter(field_name="poststed", lookup_expr="icontains")
    postnummer = filters.CharFilter(field_name="postnummer", lookup_expr="exact")

    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("poststed", "poststed"),
            ("created_at", "created_at"),
        ),
        help_text='Order by field. Use "-" for descending (e.g., "-name")',
    )

    class Meta:
        model = Leverandorer
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            models.Q(name__icontains=value)
            | models.Q(addresse__icontains=value)
            | models.Q(poststed__icontains=value)
            | models.Q(epost__icontains=value)
        ).distinct()


class JobberFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search", help_text="Search jobs")
    tittel = filters.CharFilter(field_name="tittel", lookup_expr="icontains")
    adresse = filters.CharFilter(field_name="adresse", lookup_expr="icontains")
    ferdig = filters.BooleanFilter(field_name="ferdig")

    # Date filtering
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    date_after = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    date_before = filters.DateTimeFilter(field_name="date", lookup_expr="lte")

    ordering = filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("date", "date"),
            ("ordre_nr", "ordre_nr"),
            ("tittel", "tittel"),
        ),
        help_text='Order by field. Use "-" for descending (e.g., "-created_at")',
    )

    class Meta:
        model = Jobber
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            models.Q(tittel__icontains=value)
            | models.Q(adresse__icontains=value)
            | models.Q(beskrivelse__icontains=value)
            | models.Q(ordre_nr__icontains=value)
        ).distinct()


class JobbMatriellFilter(filters.FilterSet):
    search = filters.CharFilter(
        method="filter_search", help_text="Search job materials"
    )
    jobb = filters.ModelChoiceFilter(
        field_name="jobb", queryset=Jobber.objects.all(), to_field_name="ordre_nr"
    )
    matriell_el_nr = filters.CharFilter(
        field_name="matriell__el_nr", lookup_expr="exact"
    )
    transf = filters.BooleanFilter(field_name="transf")
    antall_min = filters.NumberFilter(field_name="antall", lookup_expr="gte")
    antall_max = filters.NumberFilter(field_name="antall", lookup_expr="lte")

    ordering = filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("antall", "antall"),
            ("matriell__el_nr", "matriell_el_nr"),
        ),
        help_text='Order by field. Use "-" for descending',
    )

    class Meta:
        model = JobbMatriell
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            models.Q(matriell__el_nr__icontains=value)
            | models.Q(matriell__tittel__icontains=value)
            | models.Q(jobb__tittel__icontains=value)
        ).distinct()


class TimelisteFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search", help_text="Search time entries")
    user = filters.ModelChoiceFilter(field_name="user", queryset=User.objects.all())
    jobb = filters.ModelChoiceFilter(
        field_name="jobb", queryset=Jobber.objects.all(), to_field_name="ordre_nr"
    )
    dato_after = filters.DateFilter(field_name="dato", lookup_expr="gte")
    dato_before = filters.DateFilter(field_name="dato", lookup_expr="lte")
    timer_min = filters.NumberFilter(field_name="timer", lookup_expr="gte")
    timer_max = filters.NumberFilter(field_name="timer", lookup_expr="lte")

    # This month/week filters
    this_month = filters.BooleanFilter(method="filter_this_month")
    this_week = filters.BooleanFilter(method="filter_this_week")

    ordering = filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("dato", "dato"),
            ("timer", "timer"),
        ),
        help_text='Order by field. Use "-" for descending',
    )

    class Meta:
        model = Timeliste
        fields = []

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            models.Q(beskrivelse__icontains=value)
            | models.Q(jobb__tittel__icontains=value)
            | models.Q(user__username__icontains=value)
        ).distinct()

    def filter_this_month(self, queryset, name, value):
        if value:
            now = timezone.now()
            return queryset.filter(dato__month=now.month, dato__year=now.year)
        return queryset

    def filter_this_week(self, queryset, name, value):
        if value:
            now = timezone.now()
            start_week = now - timezone.timedelta(days=now.weekday())
            end_week = start_week + timezone.timedelta(days=6)
            return queryset.filter(dato__range=[start_week.date(), end_week.date()])
        return queryset
