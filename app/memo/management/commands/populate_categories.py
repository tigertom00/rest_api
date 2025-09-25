from django.core.management.base import BaseCommand

from app.memo.models import ElektriskKategori


class Command(BaseCommand):
    help = "Populate initial electrical categories based on Norwegian electrical numbering system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        initial_categories = [
            {
                "blokknummer": "10",
                "kategori": "Kabler og ledninger",
                "beskrivelse": "Installasjonskabler, PR-kabler, fleksible kabler, varmekabler, fiberkabler og spesialkabler for inne/ute/industri.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "11",
                "kategori": "Ledningsføringsprodukter",
                "beskrivelse": "Rør, kanaler, kabelstiger, kabelskinner, kabelbeskyttere og monteringsutstyr for ledningsføringer.",
                "etim_gruppe": "EC001xxx",
            },
            {
                "blokknummer": "12",
                "kategori": "Installasjonsutstyr",
                "beskrivelse": "Bokser, rørfester, kabelsko, endehylser, klemmer og tilbehør for montering av kabler og ledninger.",
                "etim_gruppe": "EC002xxx",
            },
            {
                "blokknummer": "13",
                "kategori": "Brytere og kontakter",
                "beskrivelse": "Veggkontakter, lysbrytere, trykkknapper, dimmere og automatsikringer (MCB).",
                "etim_gruppe": "EC000517",
            },
            {
                "blokknummer": "14",
                "kategori": "Styring og automasjon",
                "beskrivelse": "Reléer, tidshendelser, sensorer, PLC-komponenter og automasjonsutstyr.",
                "etim_gruppe": "EC001744",
            },
            {
                "blokknummer": "15",
                "kategori": "Jording og lynvern",
                "beskrivelse": "Jordingsutstyr, overspenningsvern, lynavledere og beskyttelseskomponenter.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "20",
                "kategori": "Belysning og lyskilder",
                "beskrivelse": "Lamper, LED-moduler, armaturer, lysrør og belysningskomponenter.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "30",
                "kategori": "Sikring og distribusjon",
                "beskrivelse": "Sikringsholdere, fordelere, strømskinner og transformatorer.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "40",
                "kategori": "Lavspenning og transformasjon",
                "beskrivelse": "Lavvolt-forsyninger, transformatorer og DC/AC-konvertere.",
                "etim_gruppe": "EC000000",
            },
            {
                "blokknummer": "50",
                "kategori": "Måle- og kontrollinstrumenter",
                "beskrivelse": "Multimetre, spenningsmålere, termostater og overvåkningsutstyr.",
                "etim_gruppe": "EC001855",
            },
        ]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        created_count = 0
        updated_count = 0

        for category_data in initial_categories:
            blokknummer = category_data["blokknummer"]

            if dry_run:
                existing = ElektriskKategori.objects.filter(
                    blokknummer=blokknummer
                ).exists()
                if existing:
                    self.stdout.write(
                        f"Would update: {blokknummer} - {category_data['kategori']}"
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f"Would create: {blokknummer} - {category_data['kategori']}"
                    )
                    created_count += 1
            else:
                category, created = ElektriskKategori.objects.get_or_create(
                    blokknummer=blokknummer, defaults=category_data
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created: {category}"))
                    created_count += 1
                else:
                    # Update existing category with new data
                    for field, value in category_data.items():
                        if field != "blokknummer":
                            setattr(category, field, value)
                    category.save()
                    self.stdout.write(self.style.WARNING(f"Updated: {category}"))
                    updated_count += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN COMPLETE - Would create {created_count} and update {updated_count} categories"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {created_count} and updated {updated_count} electrical categories"
                )
            )
