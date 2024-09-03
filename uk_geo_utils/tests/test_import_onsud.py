import os
from io import StringIO

from django.test import TestCase

from uk_geo_utils.management.commands.import_onsud import Command
from uk_geo_utils.models import Onsud


class OnsudImportTest(TestCase):
    def test_import_onsud_valid(self):
        # check table is empty before we start
        self.assertEqual(0, Onsud.objects.count())

        # path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "../fixtures/onsud"
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        # import data
        opts = {"path": csv_path, "transaction": False}
        cmd.handle(**opts)

        # ensure all our tasty data has been imported
        self.assertEqual(4, Onsud.objects.count())

    def test_import_onsud_file_not_found(self):
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/pathdoesnotexist",
            )
        )

        cmd = Command()

        # supress output
        cmd.stdout = StringIO()

        opts = {"path": csv_path, "transaction": False}
        with self.assertRaises(FileNotFoundError):
            cmd.handle(**opts)
