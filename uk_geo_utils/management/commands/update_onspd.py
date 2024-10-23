from uk_geo_utils.base_updater import BaseUpdater
from uk_geo_utils.helpers import get_onspd_model
from uk_geo_utils.management.commands.import_onspd import (
    HEADERS,
)
from uk_geo_utils.management.commands.import_onspd import (
    Command as LocalImporter,
)


class Command(BaseUpdater):
    """
    Usage: python manage.py update_onspd --data-path /home/will/Downloads/ONSPD_MAY_2024/Data
    """

    def get_table_name(self):
        return get_onspd_model()._meta.db_table

    def get_importer(self):
        cmd = LocalImporter()
        cmd.table_name = self.temp_table_name
        cmd.path = self.data_path
        cmd.header = HEADERS["aug2022"]
        return cmd

    def run_importer(self, cmd):
        cmd.import_onspd()
