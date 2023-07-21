import os
from django.db import connection
from django.db import transaction
from django.core.management.base import BaseCommand
from uk_geo_utils.helpers import get_address_model


class Command(BaseCommand):
    help = (
        "Deletes all data in Address model AND any related tables,",
        "and replaces Address model data with that in the cleaned AddressBase CSVs.",
        "Data in related tables will need to be imported/rebuilt seperately",
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "cleaned_ab_path",
            help="The path to the folder containing the cleaned AddressBase CSVs",
        )
        parser.add_argument(
            "-t",
            "--transaction",
            help="Run the import in a transaction",
            action="store_true",
            default=False,
            dest="transaction",
        )

    def handle(self, *args, **kwargs):
        self.table_name = get_address_model()._meta.db_table
        self.path = kwargs["cleaned_ab_path"]
        if kwargs["transaction"]:
            with transaction.atomic():
                self.import_addressbase()
        else:
            self.import_addressbase()

    def import_addressbase(self):
        cleaned_file_path = os.path.abspath(
            os.path.join(self.path, "addressbase_cleaned.csv")
        )

        with open(cleaned_file_path, "r") as fp:
            cursor = connection.cursor()
            self.stdout.write("clearing existing data..")
            cursor.execute("TRUNCATE TABLE %s CASCADE;" % (self.table_name))

            self.stdout.write("importing from %s.." % (cleaned_file_path))
            cursor.copy_expert(
                """
                COPY %s (UPRN,address,postcode,location,addressbase_postal)
                FROM STDIN (FORMAT CSV, DELIMITER ',', quote '"');
            """
                % (self.table_name),
                fp,
            )

        self.stdout.write("...done")
