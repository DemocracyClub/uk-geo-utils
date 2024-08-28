import csv
import os
import re
from io import StringIO

from django.test import TestCase

from uk_geo_utils.management.commands.clean_addressbase_plus import Command


class CleanAddressesTest(TestCase):
    def test_clean_addresses_valid(self):
        # path to files we're going to process
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/addressbase_plus",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        # import data
        opts = {"ab_path": csv_path}
        cmd.handle(**opts)

        expected_outfile = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/addressbase_plus/addressbase_cleaned.csv",
            )
        )

        self.assertTrue(os.path.isfile(expected_outfile))

        with open(expected_outfile) as csvfile:
            content = csvfile.readlines()
            self.assertEqual(9, len(content))

        with open(expected_outfile) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.assertEqual(5, len(row))
                self.assertTrue(row[0].startswith("1000000000"))
                self.assertTrue(
                    re.match(
                        r"SRID=4326;POINT\(-?\d*.?\d+ -?\d*.?\d+\)", row[3]
                    )
                )

    def test_clean_addresses_file_not_found(self):
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/pathdoesnotexist",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        opts = {"ab_path": csv_path}
        with self.assertRaises(FileNotFoundError):
            cmd.handle(**opts)
