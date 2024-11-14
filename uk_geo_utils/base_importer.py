import abc
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import psutil
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections, transaction


def unzip(filepath):
    zip_file = zipfile.ZipFile(filepath, "r")
    tmpdir = tempfile.mkdtemp()
    zip_file.extractall(tmpdir)
    return tmpdir


def check_memory(required_memory: int = 2):
    # Downloading, unzipping and working with the ONSPD
    # requires a decent chunk of memory to play with.
    # Running this import on a tiny instance like a
    # t2.micro will cause an Out Of Memory error

    # By default ensure we've got >2Gb total before we start
    mem = psutil.virtual_memory()
    gb = ((mem.total / 1024) / 1024) / 1024
    return gb >= required_memory


class BaseImporter(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foreign_key_constraints = None
        self.indexes = None
        self.primary_key_constraint = None
        self.tempdir = None
        self.data_path = None
        self.cursor = None
        self.table_name = self.get_table_name()
        self.temp_table_name = self.table_name + "_temp"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--url", action="store")
        group.add_argument("--data-path", action="store")
        parser.add_argument("--database", default=DEFAULT_DB_ALIAS)

    @abc.abstractmethod
    def get_table_name(self) -> str:
        pass

    def get_data_path(self, options):
        data_path = None

        if options.get("data_path"):
            self.data_path = options["data_path"]

        if url := options.get("url"):
            self.stdout.write(f"Downloading data from {url}")
            tmp = tempfile.NamedTemporaryFile()
            urllib.request.urlretrieve(url, tmp.name)
            self.tempdir = unzip(tmp.name)
            self.data_path = Path(self.tempdir) / "Data"

        return data_path

    @abc.abstractmethod
    def import_data_to_temp_table(self):
        pass

    def get_index_statements(self):
        self.cursor.execute(f"""
            SELECT tablename, indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename='{self.table_name}' 
        """)
        results = self.cursor.fetchall()

        indexes = []
        for row in results:
            original_index_name = row[1]
            original_index_create_statement = row[2]
            temp_index_name = original_index_name + "_temp"
            temp_index_create_statement = self.make_temp_index_create_statement(
                original_index_create_statement,
                original_index_name,
                temp_index_name,
            )
            rename_temp_index_statement = (
                f"ALTER INDEX {temp_index_name} RENAME TO {original_index_name}"
            )
            indexes.append(
                {
                    "index_name": original_index_name,
                    "temp_index_name": temp_index_name,
                    "original_index_create_statement": original_index_create_statement,
                    "temp_index_create_statement": temp_index_create_statement,
                    "rename_temp_index_statement": rename_temp_index_statement,
                }
            )

        return indexes

    def make_temp_index_create_statement(
        self,
        original_index_create_statement,
        original_index_name,
        temp_index_name,
    ):
        # we expect the statement to be of the form
        # CREATE [UNIQUE] INDEX $index ON $table USING $fields"
        temp_index_create_statement = original_index_create_statement.replace(
            f"INDEX {original_index_name}",
            f"INDEX IF NOT EXISTS {temp_index_name}",
        )
        return temp_index_create_statement.replace(
            f"ON public.{self.table_name}", f"ON public.{self.temp_table_name}"
        )

    def build_temp_indexes(self):
        self.stdout.write(f"Building indexes on {self.temp_table_name}...")
        for index in self.indexes:
            self.stdout.write(
                f"Executing: {index['temp_index_create_statement']}"
            )
            self.cursor.execute(index["temp_index_create_statement"])

    def get_primary_key_constraint(self):
        pkey_sql = f"""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = '{self.table_name}'::regclass AND contype = 'p';
        """
        self.cursor.execute(pkey_sql)
        results = self.cursor.fetchall()
        num_keys = len(results)
        if num_keys != 1:
            raise ValueError(
                f"Expected there to be 1 primary key. But {num_keys} found."
            )

        self.stdout.write("Found primary key constraint")
        constraint_name = results[0][0]
        temp_name = constraint_name + "_temp"
        constraintdef = results[0][1]
        return {
            "constraint_name": constraint_name,
            "temp_name": temp_name,
            "constraintdef": constraintdef,
            "temp_constraint_create_statement": f"ALTER TABLE {self.temp_table_name} ADD CONSTRAINT {temp_name} {constraintdef}",
        }

    def add_temp_primary_key(self):
        self.stdout.write(f"Adding primary key to {self.temp_table_name}...")
        self.stdout.write(
            f"Executing: {self.primary_key_constraint['temp_constraint_create_statement']}"
        )
        self.cursor.execute(
            self.primary_key_constraint["temp_constraint_create_statement"]
        )

    def get_foreign_key_constraints(self):
        fkey_sql = f"""
            SELECT conname AS constraint_name, confrelid::regclass::text AS refrenced_table, pg_get_constraintdef(oid), conrelid::regclass::text AS referencing_table
            FROM pg_constraint 
            WHERE contype = 'f'
                AND (
                    conrelid = '{self.table_name}'::regclass 
                    OR
                    confrelid = '{self.table_name}'::regclass
                )      
        """
        self.cursor.execute(fkey_sql)
        results = self.cursor.fetchall()

        self.stdout.write(
            f"Found {len(results)} foreign key constraints, where {self.table_name} is the referencing or referenced table"
        )

        fk_constraints = []
        seen = set()

        for row in results:
            constraint_name = row[0]
            if constraint_name not in seen:
                seen.add(constraint_name)
                # referenced_table_name = row[1]
                constraintdef = row[2]
                referencing_table = row[3]

                fk_constraints.append(
                    {
                        "constraint_name": constraint_name,
                        "create_statement": f"ALTER TABLE {referencing_table} ADD CONSTRAINT {constraint_name} {constraintdef}",
                        "delete_statement": f"ALTER TABLE {referencing_table} DROP CONSTRAINT IF EXISTS {constraint_name}",
                    }
                )

        return fk_constraints

    def drop_foreign_keys(self):
        self.stdout.write("Dropping foreign keys...")
        for constraint in self.foreign_key_constraints:
            self.stdout.write(f"Executing: {constraint['delete_statement']}")
            self.cursor.execute(constraint["delete_statement"])

    def check_foreign_key_exists(self, constraint_name):
        # This check is especially useful when we're importing addressbase and uprntocouncil in WDIV.
        # This is because there is a fk from one to the other, so they both pick up the same fk.
        # You can't do a try/except on the create because then any subsequent commands will fail with
        # SQLSTATE code:
        #  > The 25P02 error code in PostgreSQL is associated with the “in_failed_sql_transaction” state.
        #  > This error indicates that you are trying to execute an SQL command after a previous command
        #  > in the same transaction has failed. Once a transaction encounters an error, it becomes ‘tainted’,
        #  > and PostgreSQL will not allow any further SQL commands to be executed until the transaction is
        #  > either rolled back or the failed command is resolved with a savepoint.
        # https://philipmcclarence.com/how-to-diagnose-and-fix-the-25p02-in_failed_sql_transaction-error-code-in-postgres/

        self.cursor.execute(f"""
            SELECT 1
            FROM pg_constraint 
            WHERE contype = 'f'
                AND conname = '{constraint_name}'
        """)
        return bool(self.cursor.fetchone())

    def add_foreign_keys(self):
        self.stdout.write("Creating foreign keys...")
        for constraint in self.foreign_key_constraints:
            if self.check_foreign_key_exists(constraint["constraint_name"]):
                self.stdout.write(
                    f"Foreign key {constraint['constraint_name']} already exists - skipping"
                )
                continue

            self.stdout.write(f"Executing: {constraint['create_statement']}")
            self.cursor.execute(constraint["create_statement"])

    def create_temp_table(self):
        self.stdout.write(
            f"Creating temp table called {self.temp_table_name}..."
        )
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.temp_table_name};")
        self.cursor.execute(
            f"CREATE UNLOGGED TABLE {self.temp_table_name} AS SELECT * FROM {self.table_name} LIMIT 0;"
        )

    def drop_old_table(self):
        self.stdout.write("Dropping old table...")
        drop_table_statement = f"DROP TABLE {self.table_name} CASCADE "
        self.stdout.write(f"Executing: {drop_table_statement}")
        self.cursor.execute(drop_table_statement)

    def rename_temp_table(self):
        self.stdout.write("Renaming temp table...")
        rename_table_statement = (
            f"ALTER TABLE {self.temp_table_name} RENAME TO {self.table_name}"
        )
        self.stdout.write(f"Executing: {rename_table_statement}")
        self.cursor.execute(rename_table_statement)
        self.stdout.write("Renaming primary key...")
        primary_key_rename_statement = f"ALTER TABLE {self.table_name} RENAME CONSTRAINT {self.primary_key_constraint['temp_name']} TO {self.primary_key_constraint['constraint_name']}"
        self.stdout.write(f"Executing: {primary_key_rename_statement}")
        self.cursor.execute(primary_key_rename_statement)
        self.rename_temp_indexes()

    def rename_temp_indexes(self):
        index_rename_statements = []
        for index in self.indexes:
            if (
                index["index_name"]
                == self.primary_key_constraint["constraint_name"]
            ):
                self.stdout.write(
                    f"Skipping rename of {index['index_name']} because renaming primary key constraint renamed it already"
                )
            else:
                index_rename_statements.append(
                    index["rename_temp_index_statement"]
                )

        for statement in index_rename_statements:
            self.stdout.write(f"Executing: {statement}")
            self.cursor.execute(statement)

    def check_for_other_constraints(self):
        self.stdout.write(
            "Checking for non primary key/foreign key constraints..."
        )
        self.cursor.execute(f"""
            SELECT 1
            FROM pg_constraint
            WHERE
                contype NOT IN ('p', 'f')
                AND
                conrelid = '{self.table_name}'::regclass;
        """)
        result = self.cursor.fetchone()
        if result:
            raise (
                Exception(
                    "Non primary key/foreign key constraints found. Aborting import, to avoid overwriting."
                )
            )
        self.stdout.write("...none found. Continuing.")

    def get_constraints_and_index_statements(self):
        self.stdout.write(
            f"Getting constraints and indexes for {self.table_name}"
        )
        self.primary_key_constraint = self.get_primary_key_constraint()
        self.indexes = self.get_index_statements()
        self.foreign_key_constraints = self.get_foreign_key_constraints()
        self.check_for_other_constraints()

    def handle(self, *args, **options):
        if not check_memory():
            raise Exception(
                "This instance has less than the recommended memory. Try running the import from a larger instance."
            )

        db_name = options["database"]
        self.cursor = connections[db_name].cursor()

        self.get_data_path(options)

        self.get_constraints_and_index_statements()

        try:
            # Create empty temp tables
            self.create_temp_table()

            # import data into the temp table
            self.import_data_to_temp_table()

            # Add temp primary keys
            self.add_temp_primary_key()

            # Add temp indexes
            self.build_temp_indexes()

            with transaction.atomic():
                # Drop Foreign keys
                if self.foreign_key_constraints:
                    self.drop_foreign_keys()

                # drop old table
                self.drop_old_table()

                # Rename temp table to original names, pkey and indexes
                self.rename_temp_table()

                # Add Foreign keys
                if self.foreign_key_constraints:
                    self.add_foreign_keys()

        finally:
            self.db_cleanup()
            self.file_cleanup()

        self.stdout.write("...done")

    def db_cleanup(self):
        self.stdout.write("Dropping temp table if exists...")
        self.cursor.execute(
            f"DROP TABLE IF EXISTS {self.temp_table_name} CASCADE;"
        )

    def file_cleanup(self):
        if self.tempdir:
            self.stdout.write(f"Cleaning up temp files in {self.tempdir}")
            try:
                shutil.rmtree(self.tempdir)
            except OSError:
                self.stdout.write("Failed to clean up temp files.")
