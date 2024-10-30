import os
from io import StringIO
from unittest.mock import patch

from django.db import connection
from django.test import TestCase

from uk_geo_utils.management.commands.import_cleaned_addresses import Command
from uk_geo_utils.models import Address


def create_uprntocouncil_table():
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE uk_geo_utils_uprntocouncil (
                uprn character varying(12) NOT NULL PRIMARY KEY,
                lad character varying(9),
                polling_station_id character varying(255),
                CONSTRAINT uprntocouncil_uprn_fk FOREIGN KEY (uprn)
                    REFERENCES uk_geo_utils_address (uprn) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            INSERT INTO uk_geo_utils_uprntocouncil (uprn, lad, polling_station_id)
            VALUES
                ('123456789', 'E07000223', ''),
                ('9876543210', 'E07000070', '');
        """)


def get_foreign_key_name(table):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = '{table}'::regclass
            AND contype = 'f';
        """)
        return cursor.fetchone()[0]


def get_primary_key_name(table):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = '{table}'::regclass
            AND contype = 'p';
        """)
        return cursor.fetchone()[0]


def count_uprntocouncil_records():
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM uk_geo_utils_uprntocouncil")
        return cursor.fetchone()[0]


def get_uprntoconcil_record(uprn):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT lad, polling_station_id
            FROM uk_geo_utils_uprntocouncil
            WHERE uprn = '{uprn}';
        """
        )
        return cursor.fetchone()


class AddressImportTransactionTest(TestCase):
    def setUp(self):
        # Create some initial addresses
        self.initial_addresses = [
            Address.objects.create(
                uprn="123456789",
                address="10 Test Street",
                postcode="TE5 1ST",
                location="POINT(0 0)",
                addressbase_postal="D",
            ),
            Address.objects.create(
                uprn="9876543210",
                address="20 Test Avenue",
                postcode="TE5 2ND",
                location="POINT(1 1)",
                addressbase_postal="D",
            ),
        ]

        # Create the UprnToCouncil table
        create_uprntocouncil_table()

        # Store initial primary key name
        self.initial_pk_name = get_primary_key_name("uk_geo_utils_address")

    def test_transaction_rollback_on_failure(self):
        # check counts before we start
        self.assertEqual(2, Address.objects.count())
        self.assertEqual(2, count_uprntocouncil_records())

        # path to file we're going to import
        csv_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../fixtures/cleaned_addresses",
            )
        )

        # setup command
        cmd = Command()
        opts = {"data_path": csv_path}

        # supress output
        cmd.stdout = StringIO()

        # Mock rename_temp_table to simulate a failure during transaction
        with patch.object(
            Command, "rename_temp_table"
        ) as mock_rename_temp_table:
            mock_rename_temp_table.side_effect = Exception(
                "Oh no... Something went wrong renaming the temp tables"
            )

            # Run import and expect it to fail
            with self.assertRaises(Exception) as context:
                cmd.handle(**opts)
                self.assertEqual(
                    str(context.exception),
                    "Oh no... Something went wrong renaming the temp tables",
                )

            # Verify original data is intact
            self.assertEqual(
                Address.objects.count(),
                2,
                "Number of addresses should be unchanged after failed import",
            )

            self.assertEqual(
                count_uprntocouncil_records(),
                2,
                "Number of council links should be unchanged after failed import",
            )

            # Verify the specific records are unchanged
            for address in self.initial_addresses:
                db_address = Address.objects.get(uprn=address.uprn)
                self.assertEqual(
                    db_address.address,
                    address.address,
                    f"Address {address.uprn} was modified despite transaction rollback",
                )

            # Verify uprn records are intact
            record_1 = get_uprntoconcil_record("123456789")
            self.assertEqual(record_1[0], "E07000223")
            self.assertEqual(record_1[1], "")

            record_2 = get_uprntoconcil_record("9876543210")
            self.assertEqual(record_2[0], "E07000070")
            self.assertEqual(record_2[1], "")

            # Verify temp table was cleaned up
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT tablename FROM pg_tables WHERE schemaname = 'public'"""
                )
                tables = cursor.fetchall()
                tables.sort()
                expected_tables = [
                    ("spatial_ref_sys",),
                    ("django_migrations",),
                    ("uk_geo_utils_address",),
                    ("uk_geo_utils_onsud",),
                    ("uk_geo_utils_onspd",),
                    ("uk_geo_utils_uprntocouncil",),
                ]
                expected_tables.sort()
                self.assertListEqual(
                    tables,
                    expected_tables,
                )

            # Verify primary key name is unchanged
            current_pk_name = get_primary_key_name("uk_geo_utils_address")
            self.assertEqual(
                current_pk_name,
                self.initial_pk_name,
                "Primary key constraint name should be unchanged after rollback",
            )

            # Verify foreign key name is unchanged
            current_fk_name = get_foreign_key_name("uk_geo_utils_uprntocouncil")
            self.assertEqual(
                current_fk_name,
                "uprntocouncil_uprn_fk",
                "Foreign key constraint name should be unchanged after rollback",
            )
