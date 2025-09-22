import csv
import os
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.memo.models import Leverandorer, Matriell


class Command(BaseCommand):
    help = 'Import Norwegian electrical components database from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing electrical components data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of rows to import (for testing)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        limit = options['limit']

        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file "{csv_file}" does not exist.')

        self.stdout.write(f'Reading CSV file: {csv_file}')

        manufacturers = {}
        imported_count = 0
        skipped_count = 0
        error_count = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                with transaction.atomic():
                    for row_num, row in enumerate(reader, 1):
                        if limit and row_num > limit:
                            break

                        try:
                            # Process manufacturer
                            manufacturer_name = row.get('FABRIKAT', '').strip()
                            leverandor = None

                            if manufacturer_name:
                                if manufacturer_name not in manufacturers:
                                    if not dry_run:
                                        leverandor, created = Leverandorer.objects.get_or_create(
                                            manufacturer_code=manufacturer_name,
                                            defaults={'name': manufacturer_name}
                                        )
                                        manufacturers[manufacturer_name] = leverandor
                                        if created:
                                            self.stdout.write(f'Created manufacturer: {manufacturer_name}')
                                    else:
                                        manufacturers[manufacturer_name] = f'Would create: {manufacturer_name}'
                                else:
                                    leverandor = manufacturers[manufacturer_name]

                            # Process electrical component
                            el_nr = row.get('ELNUMMER', '').strip() or row.get('ELNUMMER_NO', '').strip()

                            if not el_nr:
                                skipped_count += 1
                                continue

                            # Check if component already exists
                            if not dry_run and Matriell.objects.filter(el_nr=el_nr).exists():
                                skipped_count += 1
                                continue

                            # Prepare component data
                            component_data = self.prepare_component_data(row, leverandor)

                            if dry_run:
                                self.stdout.write(f'Would import: {el_nr} - {component_data["tittel"][:50]}...')
                            else:
                                Matriell.objects.create(**component_data)

                            imported_count += 1

                            if imported_count % 1000 == 0:
                                self.stdout.write(f'Processed {imported_count} components...')

                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Error processing row {row_num}: {str(e)}')
                            )
                            continue

                    if dry_run:
                        # Rollback transaction for dry run
                        transaction.set_rollback(True)

        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')

        # Summary
        action = 'Would import' if dry_run else 'Imported'
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{action} {imported_count} components\n'
                f'Skipped: {skipped_count}\n'
                f'Errors: {error_count}\n'
                f'Manufacturers processed: {len(manufacturers)}'
            )
        )

    def prepare_component_data(self, row, leverandor):
        """Prepare component data from CSV row"""

        def safe_decimal(value, default=None):
            """Safely convert string to Decimal"""
            if not value or value.strip() == '':
                return default
            try:
                return Decimal(value.replace(',', '.'))
            except (InvalidOperation, ValueError):
                return default

        def safe_bool(value):
            """Safely convert string to boolean"""
            if isinstance(value, str):
                return value.strip() == '1' or value.strip().lower() == 'true'
            return bool(value)

        # Get Norwegian description (prefer BESKR_NO, fallback to BESKR)
        norwegian_desc = row.get('BESKR_NO', '').strip() or row.get('BESKR', '').strip()

        return {
            'el_nr': row.get('ELNUMMER', '').strip() or row.get('ELNUMMER_NO', '').strip(),
            'tittel': norwegian_desc[:255],  # Use Norwegian description as title
            'info': row.get('BEMERKNING', '').strip()[:256],
            'leverandor': leverandor if not isinstance(leverandor, str) else None,

            # New fields from electrical database
            'ean_number': row.get('EANNUMMER', '').strip()[:32],
            'article_number': row.get('VARENUMMER', '').strip()[:32],
            'order_number': row.get('BESTILNR', '').strip()[:100],
            'type_designation': row.get('TYPE', '').strip()[:255],
            'norwegian_description': norwegian_desc[:255],
            'english_description': row.get('DESCRIPT', '').strip()[:255],
            'german_description': row.get('BESCHR', '').strip()[:255],
            'category': row.get('VAREGRUPPE', '').strip()[:10],
            'datasheet_url': row.get('DATABLAD', '').strip()[:200],
            'list_price': safe_decimal(row.get('LISTEPRIS', '')),
            'net_price': safe_decimal(row.get('NETTOPRIS', '')),
            'discount_factor': row.get('RABATTFAKT', '').strip()[:4],
            'vat': row.get('MVA', '').strip()[:5],
            'weight': row.get('BRUTTOVEKT', '').strip()[:8],
            'unit_per_package': row.get('ENHETPRPAK', '').strip()[:5],
            'height': row.get('HEIGHT', '').strip()[:20],
            'width': row.get('WIDTH', '').strip()[:20],
            'depth': row.get('DEPTH', '').strip()[:20],
            'approved': safe_bool(row.get('GODKJENT', False)),
            'discontinued': safe_bool(row.get('UTGÅTT', False)),
        }