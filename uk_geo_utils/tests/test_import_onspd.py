import os
from io import StringIO

from django.contrib.gis.geos import Point
from django.test import TestCase

from uk_geo_utils.management.commands.import_onspd import Command
from uk_geo_utils.models import Onspd


class May2018OnspdImportTest(TestCase):
    def test_import_onspd_valid(self):
        # check table is empty before we start
        self.assertEqual(0, Onspd.objects.count())

        # path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/onspd_may2018",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        # import data
        opts = {
            "data_path": csv_path,
            "header": "may2018",
        }

        cmd.handle(**opts)

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


class Aug2022OnspdImportTest(TestCase):
    def test_import_onspd_valid(self):
        # check table is empty before we start
        self.assertEqual(0, Onspd.objects.count())

        # path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/onspd_aug2022",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        # import data
        opts = {
            "data_path": csv_path,
            "header": "aug2022",
        }
        cmd.handle(**opts)

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

        opts = {
            "data_path": csv_path,
            "header": "aug2022",
        }
        with self.assertRaises(FileNotFoundError):
            cmd.handle(**opts)
