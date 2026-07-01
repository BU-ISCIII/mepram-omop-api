import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.api.services.dashboard_models import DASHBOARD_MODELS

import json


COPY_RE = re.compile(r"^COPY dashboard\.([^\s(]+) \(([^)]+)\) FROM stdin;$")
TABLE_MODELS = {model._meta.db_table: model for model in DASHBOARD_MODELS}


def parse_copy_value(value):
    if isinstance(value, dict):
        return value
    if value == r"\N":
        return None

    replacements = {
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
        "\\": "\\",
    }
    result = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value):
            index += 1
            result.append(replacements.get(value[index], value[index]))
        else:
            result.append(char)
        index += 1
    return "".join(result)


class Command(BaseCommand):
    help = "Import dashboard COPY blocks from a PostgreSQL dump into Django-managed tables."

    def add_arguments(self, parser):
        parser.add_argument("sql_path", help="Path to dashboard.sql")
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete existing dashboard rows before importing",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Rows inserted per bulk_create batch",
        )

    def handle(self, *args, **options):
        sql_path = Path(options["sql_path"]).expanduser().resolve()
        if not sql_path.exists():
            raise CommandError(f"SQL file not found: {sql_path}")

        if options["truncate"]:
            self._truncate_tables()

        counts = self._import_copy_blocks(sql_path, options["batch_size"])
        for table_name, row_count in counts.items():
            self.stdout.write(
                self.style.SUCCESS(f"Imported {row_count} rows into {table_name}")
            )

    def _truncate_tables(self):
        for model in reversed(DASHBOARD_MODELS):
            deleted, _ = model.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} rows from {model._meta.db_table}")

    @transaction.atomic
    def _import_copy_blocks(self, sql_path, batch_size):
        counts = {}

        with sql_path.open(encoding="utf-8") as handle:
            for line in handle:
                match = COPY_RE.match(line.rstrip("\n"))
                if not match:
                    continue

                table_name = match.group(1)
                model = TABLE_MODELS.get(table_name)
                if model is None:
                    self._skip_copy_block(handle)
                    continue

                columns = [column.strip() for column in match.group(2).split(",")]
                model_fields = {field.name for field in model._meta.fields}
                import_columns = [column for column in columns if column in model_fields]
                if len(import_columns) != len(columns):
                    unknown = sorted(set(columns) - model_fields)
                    raise CommandError(f"Unknown columns for {table_name}: {', '.join(unknown)}")

                counts[table_name] = self._load_copy_rows(
                    handle, model, import_columns, batch_size
                )

        return counts

    def _skip_copy_block(self, handle):
        for line in handle:
            if line == "\\.\n":
                return

    def _load_copy_rows(self, handle, model, columns, batch_size):
        batch = []
        row_count = 0

        for line in handle:
            if line == "\\.\n":
                if batch:
                    model.objects.bulk_create(batch, batch_size=batch_size)
                return row_count

            values = line.rstrip("\n").split("\t")
            if columns[-1] == "payload":
                values[-1] = json.loads(values[-1])

            if len(values) != len(columns):
                raise CommandError(
                    f"Invalid row for {model._meta.db_table}: "
                    f"expected {len(columns)} values"
                )

            row = dict(zip(columns, [parse_copy_value(value) for value in values]))
            batch.append(model(**row))
            row_count += 1

            if len(batch) >= batch_size:
                model.objects.bulk_create(batch, batch_size=batch_size)
                batch = []

        raise CommandError(f"Unexpected EOF while importing {model._meta.db_table}")