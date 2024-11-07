import os
from io import StringIO

from django.contrib.gis.geos import Point
from django.core.management import CommandError, call_command
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase, TransactionTestCase
from django.utils.connection import ConnectionDoesNotExist

from uk_geo_utils.management.commands.import_onspd import Command
from uk_geo_utils.models import Onspd


class OnspdImportTest(TestCase):
    def setUp(self):
        self.csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/onspd_aug2024",
            )
        )
        self.cmd = Command()
        self.cmd.stdout = StringIO()  # suppress output

    def test_import_onspd_valid(self):
        # check table is empty before we start
        self.assertEqual(0, Onspd.objects.count())

        # import data
        opts = {
            "data_path": self.csv_path,
            "database": DEFAULT_DB_ALIAS,
        }
        self.cmd.handle(**opts)

        # ensure all our tasty data has been imported
        self.assertEqual(4, Onspd.objects.count())

        # row with valid grid ref should have valid Point() location
        al11aa = Onspd.objects.filter(pcds="AL1 1AA")[0]
        self.assertEqual(
            Point(-0.341337, 51.749084, srid=4326), al11aa.location
        )

        # row with invalid grid ref should have NULL location
        im11aa = Onspd.objects.filter(pcds="IM1 1AA")[0]
        self.assertIsNone(im11aa.location)

    def test_import_onspd_header_mismatch(self):
        # path to file with old header format
        old_header_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/onspd_may2018",
            )
        )

        opts = {
            "data_path": old_header_path,
            "database": DEFAULT_DB_ALIAS,
        }
        with self.assertRaises(CommandError) as context:
            self.cmd.handle(**opts)

        # verify the error message contains our header mismatch explanation
        self.assertIn("Problem with the fields", str(context.exception))
        self.assertIn(
            "This probably means ONSPD has changed", str(context.exception)
        )

    def test_import_onspd_file_not_found(self):
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/pathdoesnotexist",
            )
        )

        opts = {"data_path": csv_path, "database": DEFAULT_DB_ALIAS}
        with self.assertRaises(FileNotFoundError):
            self.cmd.handle(**opts)


class MultiDBOnspdImportTest(TransactionTestCase):
    databases = [DEFAULT_DB_ALIAS, "other"]

    def setUp(self):
        self.csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/onspd_aug2024",
            )
        )
        self.cmd = Command()
        self.cmd.stdout = StringIO()  # suppress output

    def test_import_to_specific_database(self):
        # Check both tables are empty before we start
        self.assertEqual(0, Onspd.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(0, Onspd.objects.using("other").count())

        # Import data to 'other' database
        opts = {"data_path": self.csv_path, "database": "other"}
        self.cmd.handle(**opts)

        # Verify data was imported to 'other' database only
        self.assertEqual(0, Onspd.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(4, Onspd.objects.using("other").count())

    def test_import_to_default_database(self):
        # Check both tables are empty before we start
        self.assertEqual(0, Onspd.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(0, Onspd.objects.using("other").count())

        # Import data to default database
        opts = {
            "stdout": StringIO(),
            "data_path": self.csv_path,
        }
        call_command("import_onspd", **opts)

        # Verify data was imported to default database only
        self.assertEqual(4, Onspd.objects.using(DEFAULT_DB_ALIAS).count())
        self.assertEqual(0, Onspd.objects.using("other").count())

    def test_import_to_nonexistent_database(self):
        opts = {"data_path": self.csv_path, "database": "nonexistent_db"}

        with self.assertRaises(ConnectionDoesNotExist) as context:
            self.cmd.handle(**opts)

        self.assertEqual(
            str(context.exception),
            "The connection 'nonexistent_db' doesn't exist.",
        )
