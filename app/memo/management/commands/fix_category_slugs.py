from django.core.management.base import BaseCommand
from django.utils.text import slugify

from app.memo.models import ElektriskKategori


class Command(BaseCommand):
    help = "Fix and regenerate slugs for all electrical categories"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        categories = ElektriskKategori.objects.all()
        updated_count = 0

        for category in categories:
            old_slug = category.slug
            new_slug = slugify(category.kategori)

            if old_slug != new_slug or not old_slug:
                if dry_run:
                    self.stdout.write(
                        f"Would update {category.blokknummer} - {category.kategori}: "
                        f"'{old_slug}' -> '{new_slug}'"
                    )
                else:
                    category.slug = new_slug
                    category.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated {category.blokknummer} - {category.kategori}: "
                            f"'{old_slug}' -> '{new_slug}'"
                        )
                    )
                updated_count += 1
            else:
                self.stdout.write(
                    f"OK: {category.blokknummer} - {category.kategori} (slug: '{old_slug}')"
                )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN COMPLETE - Would update {updated_count} slugs"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {updated_count} slugs")
            )
