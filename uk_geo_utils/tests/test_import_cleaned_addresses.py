import os
from io import StringIO

from django.core import management
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase, TransactionTestCase
from django.utils.connection import ConnectionDoesNotExist

from uk_geo_utils.management.commands.import_cleaned_addresses import Command
from uk_geo_utils.models import Address


class CleanedAddressImportTest(TestCase):
    def test_import_cleaned_addresses_valid(self):
        # check table is empty before we start
        self.assertEqual(0, Address.objects.count())

        # path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/cleaned_addresses",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        # import data
        opts = {"data_path": csv_path, "database": DEFAULT_DB_ALIAS}
        cmd.handle(**opts)

        # ensure all our tasty data has been imported
        self.assertEqual(4, Address.objects.count())

    def test_import_cleaned_addresses_file_not_found(self):
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/pathdoesnotexist",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        opts = {"data_path": csv_path, "database": DEFAULT_DB_ALIAS}
        with self.assertRaises(FileNotFoundError):
            cmd.handle(**opts)


class MultiDBAddressImportTest(TransactionTestCase):
    databases = [DEFAULT_DB_ALIAS, "other"]

    def test_import_to_specific_database(self):
        # Check both tables are empty before we start
        self.assertEqual(0, Address.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(0, Address.objects.using("other").count())

        # Path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/cleaned_addresses",
            )
        )

        cmd = Command()
        cmd.stdout = StringIO()  # Suppress output

        # Import data to 'other' database
        opts = {"data_path": csv_path, "database": "other"}
        cmd.handle(**opts)

        # Verify data was imported to 'other' database only
        self.assertEqual(0, Address.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(4, Address.objects.using("other").count())

    def test_import_to_default_database(self):
        # Check both tables are empty before we start
        self.assertEqual(0, Address.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(0, Address.objects.using("other").count())

        # Path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/cleaned_addresses",
            )
        )

        # Import data to default database
        opts = {
            "stdout": StringIO(),
            "data_path": csv_path,
        }
        management.call_command("import_cleaned_addresses", **opts)

        # Verify data was imported to default database only
        self.assertEqual(4, Address.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(0, Address.objects.using("other").count())

    def test_import_to_nonexistent_database(self):
        cmd = Command()
        cmd.stdout = StringIO()  # Suppress output

        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/cleaned_addresses",
            )
        )

        opts = {"data_path": csv_path, "database": "nonexistent_db"}

        with self.assertRaises(ConnectionDoesNotExist) as context:
            cmd.handle(**opts)

        self.assertEqual(
            str(context.exception),
            "The connection 'nonexistent_db' doesn't exist.",
        )
