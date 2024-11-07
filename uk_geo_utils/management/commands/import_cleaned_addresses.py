import os

from uk_geo_utils.base_importer import BaseImporter
from uk_geo_utils.helpers import get_address_model


class Command(BaseImporter):
    help = (
        "Deletes all data in Address model AND any related tables,"
        "and replaces Address model data with that in the cleaned AddressBase CSVs."
        "Data in related tables will need to be imported/rebuilt seperately"
    )

    def get_table_name(self):
        return get_address_model()._meta.db_table

    def import_data_to_temp_table(self):
        self.import_addressbase(self.temp_table_name)

    def import_addressbase(self, table_name):
        cleaned_file_path = os.path.abspath(
            os.path.join(self.data_path, "addressbase_cleaned.csv")
        )

        with open(cleaned_file_path, "r") as fp:
            self.stdout.write("importing from %s.." % (cleaned_file_path))
            self.cursor.copy_expert(
                """
                COPY %s (UPRN,address,postcode,location,addressbase_postal)
                FROM STDIN (FORMAT CSV, DELIMITER ',', quote '"');
            """
                % (table_name),
                fp,
            )

        self.stdout.write("...done")
