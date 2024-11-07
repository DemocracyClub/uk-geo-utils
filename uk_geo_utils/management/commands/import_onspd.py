import glob
import os

from django.core.management import CommandError

from uk_geo_utils.base_importer import BaseImporter
from uk_geo_utils.helpers import get_onspd_model


class Command(BaseImporter):
    """
    To import ONSPD, grab the latest release:
    https://ons.maps.arcgis.com/home/search.html?t=content&q=ONS%20Postcode%20Directory
    and run:
        python manage.py update_onspd --data-path /path/to/ONSPD_MAY_2024/Data
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.derived_fields = ["location"]

    def get_table_name(self):
        return get_onspd_model()._meta.db_table

    def import_data_to_temp_table(self):
        self.import_onspd(self.temp_table_name)

    def check_header(self, f):
        self.stdout.write(f"checking header of {f}")
        with open(f, "r") as fp:
            # get field names from file
            header_row = fp.readline()
            file_header = sorted([f.strip() for f in header_row.split(",")])

            # get field names from db excluding derived fields (i.e. location)
            expected_header = sorted(
                [
                    field.name
                    for field in get_onspd_model()._meta.get_fields()
                    if field.name not in self.derived_fields
                ]
            )

            if file_header == expected_header:
                self.stdout.write(self.style.SUCCESS("✓ Headers match"))
                return header_row

            # find missing and unexpected fields
            missing_fields = set(expected_header) - set(file_header)
            unexpected_fields = set(file_header) - set(expected_header)

            error_msg = [
                f"\nProblem with the fields in {f}",
                f"  File header: {file_header}",
                f"  Expected header: {expected_header}",
            ]
            if missing_fields:
                error_msg.append("  Fields missing from file:")
                for field in sorted(missing_fields):
                    error_msg.append(f"  - {field}")

            if unexpected_fields:
                error_msg.append("  Unexpected fields found in file:")
                for field in sorted(unexpected_fields):
                    error_msg.append(f"  + {field}")
            error_msg.append(
                "This probably means ONSPD has changed their csv format and we need to update our model."
            )
            raise CommandError("\n".join(error_msg))

    def import_onspd(self, table_name):
        glob_str = os.path.join(self.data_path, "*.csv")
        files = glob.glob(glob_str)
        if not files:
            raise FileNotFoundError(
                "No CSV files found in %s" % (self.data_path)
            )

        self.stdout.write("importing from files..")
        for f in files:
            header = self.check_header(f)
            self.stdout.write(f"Importing {f}")
            with open(f, "r") as fp:
                self.cursor.copy_expert(
                    """
                    COPY %s (
                    %s
                    ) FROM STDIN (FORMAT CSV, DELIMITER ',', quote '"', HEADER MATCH);
                """
                    % (table_name, header),
                    fp,
                )

        # turn text lng/lat into a Point() field
        self.cursor.execute(
            """
            UPDATE %s SET location=CASE
                WHEN ("long"='0.000000' AND lat='99.999999')
                THEN NULL
                ELSE ST_GeomFromText('POINT(' || "long" || ' ' || lat || ')',4326)
            END
        """
            % (table_name)
        )

        self.stdout.write("...done")

    def handle(self, **options):
        super().handle(**options)
