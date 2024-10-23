import glob
import os

from django.db import connection

from uk_geo_utils.base_importer import BaseImporter
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


class Command(BaseImporter):
    """
    To import ONSPD, grab the latest release:
    https://ons.maps.arcgis.com/home/search.html?t=content&q=ONS%20Postcode%20Directory
    and run:
        python manage.py update_onspd --data-path /path/to/ONSPD_MAY_2024/Data
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--header",
            help="Specify which header the csv has",
            default="aug2022",
            choices=["may2018", "aug2022"],
        )

    def get_table_name(self):
        return get_onspd_model()._meta.db_table

    def import_data_to_temp_table(self):
        self.import_onspd(self.temp_table_name)

    def import_onspd(self, table_name):
        glob_str = os.path.join(self.data_path, "*.csv")
        files = glob.glob(glob_str)
        if not files:
            raise FileNotFoundError(
                "No CSV files found in %s" % (self.data_path)
            )

        cursor = connection.cursor()

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
                    % (table_name, self.header),
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
            % (table_name)
        )

        self.stdout.write("...done")

    def handle(self, **options):
        self.header = HEADERS[options.get("header", "aug2022")]

        super().handle(**options)
