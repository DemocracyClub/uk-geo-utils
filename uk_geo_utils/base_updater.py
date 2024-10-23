import abc
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import psutil
from django.core.management.base import BaseCommand
from django.db import ProgrammingError, connection, transaction


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


# noinspection SqlNoDataSourceInspection
class BaseUpdater(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foreign_key_constraints = None
        self.indexes = None
        self.primary_key_constraint = None
        self.tempdir = None
        self.data_path = None
        self.cursor = connection.cursor()
        self.table_name = self.get_table_name()
        self.temp_table_name = self.table_name + "_temp"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--url", action="store")
        group.add_argument("--data-path", action="store")

    @abc.abstractmethod
    def get_table_name(self) -> str:
        pass

    @abc.abstractmethod
    def get_importer(self):
        # make sure table name is set to temp table.
        # Can be a no-op and run_importer can implement import logic
        pass

    @abc.abstractmethod
    def run_importer(self, cmd):
        pass

    def get_data_path(self, options):
        data_path = None

        if options["data_path"]:
            self.data_path = options["data_path"]

        if url := options["url"]:
            self.stdout.write(f"Downloading data from {url}")
            tmp = tempfile.NamedTemporaryFile()
            urllib.request.urlretrieve(url, tmp.name)
            self.tempdir = unzip(tmp.name)
            self.data_path = Path(self.tempdir) / "Data"

        return data_path

    def import_data_to_temp_table(self):
        self.stdout.write("Importing data...")
        cmd = self.get_importer()
        self.run_importer(cmd)

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
            rename_old_index_statement = f"ALTER INDEX {original_index_name} RENAME TO {original_index_name}_old"
            indexes.append(
                {
                    "index_name": original_index_name,
                    "temp_index_name": temp_index_name,
                    "original_index_create_statement": original_index_create_statement,
                    "temp_index_create_statement": temp_index_create_statement,
                    "rename_temp_index_statement": rename_temp_index_statement,
                    "rename_old_index_statement": rename_old_index_statement,
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

        for row in results:
            constraint_name = row[0]
            # referenced_table_name = row[1]
            constraintdef = row[2]
            referencing_table = row[3]

            fk_constraints.append(
                {
                    "constraint_name": constraint_name,
                    "create_statement": f"ALTER TABLE {referencing_table} ADD CONSTRAINT {constraint_name} {constraintdef} NOT VALID",
                    "delete_statement": f"ALTER TABLE {referencing_table} DROP CONSTRAINT IF EXISTS {constraint_name}",
                    "validate_statement": f"ALTER TABLE {referencing_table} VALIDATE CONSTRAINT {constraint_name}",
                }
            )

        return fk_constraints

    def drop_foreign_keys(self):
        self.stdout.write("Dropping foreign keys...")
        for constraint in self.foreign_key_constraints:
            self.stdout.write(f"Executing: {constraint['delete_statement']}")
            self.cursor.execute(constraint["delete_statement"])

    def add_foreign_keys(self):
        self.stdout.write("Creating foreign keys...")
        for constraint in self.foreign_key_constraints:
            try:
                self.stdout.write(
                    f"Executing: {constraint['create_statement']}"
                )
                self.cursor.execute(constraint["create_statement"])
            except (
                ProgrammingError
            ):  # better if psycopg2.errors.DuplicateObject:
                self.stdout.write(
                    f"{constraint['constraint_name']} already exists."
                )

    def validate_foreign_keys(self):
        self.stdout.write("Validating foreign keys...")
        for constraint in self.foreign_key_constraints:
            self.stdout.write(f"Executing: {constraint['validate_statement']}")
            self.cursor.execute(constraint["validate_statement"])

    def create_temp_table(self):
        self.stdout.write(
            f"Creating temp table called {self.temp_table_name}..."
        )
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.temp_table_name};")
        self.cursor.execute(
            f"CREATE TABLE {self.temp_table_name} AS SELECT * FROM {self.table_name} LIMIT 0;"
        )

    def index_exists(self, index_name):
        self.cursor.execute(f"""
            SELECT 1 
            FROM pg_indexes 
            WHERE indexname = '{index_name}'
        """)

        return bool(self.cursor.fetchone())

    def rename_old_table(self):
        self.stdout.write("Renaming old table...")
        rename_table_statement = (
            f"ALTER TABLE {self.table_name} RENAME TO {self.table_name}_old"
        )
        self.stdout.write(f"Executing: {rename_table_statement}")
        self.cursor.execute(rename_table_statement)
        self.stdout.write("Renaming primary key...")
        primary_key_rename_statement = f"ALTER TABLE {self.table_name}_old RENAME CONSTRAINT {self.primary_key_constraint['constraint_name']} TO {self.primary_key_constraint['constraint_name']}_old"
        self.stdout.write(f"Executing: {primary_key_rename_statement}")
        self.cursor.execute(primary_key_rename_statement)

        index_rename_statements = []

        for index in self.indexes:
            if self.index_exists(index["index_name"]):
                index_rename_statements.append(
                    index["rename_old_index_statement"]
                )

        for statement in index_rename_statements:
            self.stdout.write(f"Executing: {statement}")
            self.cursor.execute(statement)

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

        index_rename_statements = []
        for index in self.indexes:
            if self.index_exists(index["temp_index_name"]):
                index_rename_statements.append(
                    index["rename_temp_index_statement"]
                )

        for statement in index_rename_statements:
            self.stdout.write(f"Executing: {statement}")
            self.cursor.execute(statement)

    def get_constraints_and_index_statements(self):
        self.stdout.write(
            f"Getting constraints and indexes for {self.table_name}"
        )
        self.primary_key_constraint = self.get_primary_key_constraint()
        self.indexes = self.get_index_statements()
        self.foreign_key_constraints = self.get_foreign_key_constraints()

    def handle(self, **options):
        if not check_memory():
            raise Exception(
                "This instance has less than the recommended memory. Try running the import from a larger instance."
            )

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

                # Rename old tables, pkeys and indexes (add _old)
                self.rename_old_table()

                # Rename temp table to original names, pkey and indexes
                self.rename_temp_table()

                # Add Foreign keys
                if self.foreign_key_constraints:
                    self.add_foreign_keys()

            # Validate foreign key constraints
            if self.foreign_key_constraints:
                self.validate_foreign_keys()

        finally:
            self.db_cleanup()
            self.file_cleanup()

        self.stdout.write("...done")

    def db_cleanup(self):
        self.stdout.write("Dropping old table if exists...")
        self.cursor.execute(
            f"DROP TABLE IF EXISTS {self.table_name}_old CASCADE;"
        )
        self.stdout.write("Dropping temp table if exists...")
        self.cursor.execute(
            f"DROP TABLE IF EXISTS {self.temp_table_name} CASCADE;"
        )

    def file_cleanup(self):
        if self.tempdir:
            try:
                shutil.rmtree(self.tempdir)
            except OSError:
                self.stdout.write("Failed to clean up temp files.")
