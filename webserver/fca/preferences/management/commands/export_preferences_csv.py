from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from fca.preferences.exporters import build_preferences_csv


class Command(BaseCommand):
    help = "Export the latest grouped faculty preference submissions to a solver-ready CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=Path,
            help="Optional output path for the generated CSV file.",
        )

    def handle(self, *args, **options):
        output_path = options.get("output") or Path("preferences_export.csv")

        try:
            csv_path = build_preferences_csv(output_path)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Preferences CSV written to {csv_path}"))
