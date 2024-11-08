import os
from io import StringIO

from django.contrib.gis.geos import Point
from django.core.management import CommandError
from django.test import TestCase

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
        self.cmd.handle(data_path=self.csv_path)

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
        old_format_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/onspd_may2018",
            )
        )

        with self.assertRaises(CommandError) as context:
            self.cmd.handle(data_path=old_format_path)

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

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        opts = {"data_path": csv_path}
        with self.assertRaises(FileNotFoundError):
            cmd.handle(**opts)
