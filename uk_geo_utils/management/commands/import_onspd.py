import glob
import os

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from uk_geo_utils.helpers import get_onspd_model

HEADERS = {
    "may2018": """
        pcd, pcd2, pcds, dointr, doterm, oscty, ced, oslaua, osward,
        parish, usertype, oseast1m, osnrth1m, osgrdind, oshlthau,
        nhser, ctry, rgn, streg, pcon, eer, teclec, ttwa, pct, nuts,
        statsward, oa01, casward, park, lsoa01, msoa01, ur01ind,
        oac01, oa11, lsoa11, msoa11, wz11, ccg, bua11, buasd11,
        ru11ind, oac11, lat, long, lep1, lep2, pfa, imd, calncv, stp
        """,
    "aug2022": """
        pcd, pcd2, pcds, dointr, doterm, oscty, ced, oslaua, osward,
        parish, usertype, oseast1m, osnrth1m, osgrdind, oshlthau,
        nhser, ctry, rgn, streg, pcon, eer, teclec, ttwa, pct, nuts,
        statsward, oa01, casward, park, lsoa01, msoa01, ur01ind,
        oac01, oa11, lsoa11, msoa11, wz11, ccg, bua11, buasd11,
        ru11ind, oac11, lat, long, lep1, lep2, pfa, imd, calncv, stp,
        oa21, lsoa21, msoa21
        """,
}


class Command(BaseCommand):
    """
    To import ONSPD, grab the latest release:
    https://ons.maps.arcgis.com/home/search.html?t=content&q=ONS%20Postcode%20Directory
    and run
    python manage.py import_onspd /path/to/data
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "path", help="Path to the directory containing the ONSPD CSVs"
        )
        parser.add_argument(
            "-t",
            "--transaction",
            help="Run the import in a transaction",
            action="store_true",
            default=False,
            dest="transaction",
        )

        parser.add_argument(
            "--header",
            help="Specify which header the csv has",
            default="aug2022",
            choices=["may2018", "aug2022"],
        )

    def handle(self, *args, **kwargs):
        self.table_name = get_onspd_model()._meta.db_table
        self.path = kwargs["path"]
        self.header = HEADERS[kwargs.get("header", "aug2022")]
        if kwargs["transaction"]:
            with transaction.atomic():
                self.import_onspd()
        else:
            self.import_onspd()

    def import_onspd(self):
        glob_str = os.path.join(self.path, "*.csv")
        files = glob.glob(glob_str)
        if not files:
            raise FileNotFoundError("No CSV files found in %s" % (self.path))

        cursor = connection.cursor()
        self.stdout.write("clearing existing data..")
        cursor.execute("TRUNCATE TABLE %s;" % (self.table_name))

        self.stdout.write("importing from files..")
        for f in files:
            self.stdout.write(f)
            with open(f, "r") as fp:
                cursor.copy_expert(
                    """
                    COPY %s (
                    %s
                    ) FROM STDIN (FORMAT CSV, DELIMITER ',', quote '"', HEADER);
                """
                    % (self.table_name, self.header),
                    fp,
                )

        # turn text lng/lat into a Point() field
        cursor.execute(
            """
            UPDATE %s SET location=CASE
                WHEN ("long"='0.000000' AND lat='99.999999')
                THEN NULL
                ELSE ST_GeomFromText('POINT(' || "long" || ' ' || lat || ')',4326)
            END
        """
            % (self.table_name)
        )

        self.stdout.write("...done")
