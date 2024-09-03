import csv
import glob
import os

from django.core.management.base import BaseCommand

from uk_geo_utils.helpers import LocalAuthAddressFormatter, PAFAddressFormatter


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "ab_path",
            help="The path to the folder containing the AddressBase CSVs",
        )

    def handle(self, *args, **kwargs):
        self.fieldnames = [
            "UPRN",
            "UDPRN",
            "CHANGE_TYPE",
            "STATE",
            "STATE_DATE",
            "CLASS",
            "PARENT_UPRN",
            "X_COORDINATE",
            "Y_COORDINATE",
            "LATITUDE",
            "LONGITUDE",
            "RPC",
            "LOCAL_CUSTODIAN_CODE",
            "COUNTRY",
            "LA_START_DATE",
            "LAST_UPDATE_DATE",
            "ENTRY_DATE",
            "RM_ORGANISATION_NAME",
            "LA_ORGANISATION",
            "DEPARTMENT_NAME",
            "LEGAL_NAME",
            "SUB_BUILDING_NAME",
            "BUILDING_NAME",
            "BUILDING_NUMBER",
            "SAO_START_NUMBER",
            "SAO_START_SUFFIX",
            "SAO_END_NUMBER",
            "SAO_END_SUFFIX",
            "SAO_TEXT",
            "ALT_LANGUAGE_SAO_TEXT",
            "PAO_START_NUMBER",
            "PAO_START_SUFFIX",
            "PAO_END_NUMBER",
            "PAO_END_SUFFIX",
            "PAO_TEXT",
            "ALT_LANGUAGE_PAO_TEXT",
            "USRN",
            "USRN_MATCH_INDICATOR",
            "AREA_NAME",
            "LEVEL",
            "OFFICIAL_FLAG",
            "OS_ADDRESS_TOID",
            "OS_ADDRESS_TOID_VERSION",
            "OS_ROADLINK_TOID",
            "OS_ROADLINK_TOID_VERSION",
            "OS_TOPO_TOID",
            "OS_TOPO_TOID_VERSION",
            "VOA_CT_RECORD",
            "VOA_NDR_RECORD",
            "STREET_DESCRIPTION",
            "ALT_LANGUAGE_STREET_DESCRIPTION",
            "DEPENDENT_THOROUGHFARE",
            "THOROUGHFARE",
            "WELSH_DEPENDENT_THOROUGHFARE",
            "WELSH_THOROUGHFARE",
            "DOUBLE_DEPENDENT_LOCALITY",
            "DEPENDENT_LOCALITY",
            "LOCALITY",
            "WELSH_DEPENDENT_LOCALITY",
            "WELSH_DOUBLE_DEPENDENT_LOCALITY",
            "TOWN_NAME",
            "ADMINISTRATIVE_AREA",
            "POST_TOWN",
            "WELSH_POST_TOWN",
            "POSTCODE",
            "POSTCODE_LOCATOR",
            "POSTCODE_TYPE",
            "DELIVERY_POINT_SUFFIX",
            "ADDRESSBASE_POSTAL",
            "PO_BOX_NUMBER",
            "WARD_CODE",
            "PARISH_CODE",
            "RM_START_DATE",
            "MULTI_OCC_COUNT",
            "VOA_NDR_P_DESC_CODE",
            "VOA_NDR_SCAT_CODE",
            "ALT_LANGUAGE",
        ]
        self.base_path = os.path.abspath(kwargs["ab_path"])
        out_path = os.path.join(self.base_path, "addressbase_cleaned.csv")

        files = glob.glob(os.path.join(self.base_path, "*.csv"))
        if not files:
            raise FileNotFoundError(
                "No CSV files found in %s" % (self.base_path)
            )

        with open(out_path, "w") as out_file:
            for csv_path in files:
                if csv_path.endswith("cleaned.csv"):
                    continue
                self.out_csv = csv.DictWriter(
                    out_file,
                    fieldnames=[
                        "UPRN",
                        "address",
                        "postcode",
                        "location",
                        "addressbase_postal",
                    ],
                )
                self.stdout.write(csv_path)
                self.clean_csv(csv_path)
                out_file.flush()

    def line_filter(self, csv_path):
        with open(csv_path) as csv_file:
            for line in csv.DictReader(csv_file, fieldnames=self.fieldnames):
                """
                - Get rid of type N UPRNs (but keep type C, D and L)
                - Get rid of records in the Isle of Man/Channel Islands
                  (but keep England, Wales, Scotland and NI)
                """
                if line["ADDRESSBASE_POSTAL"] != "N" and line["COUNTRY"] in [
                    "E",
                    "W",
                    "S",
                    "N",
                ]:
                    yield line

    def clean_csv(self, csv_path):
        for line in self.line_filter(csv_path):
            self.out_csv.writerow(self.clean_output_line(line))

    def clean_address(self, line):
        if line["ADDRESSBASE_POSTAL"] == "D":
            address_fields = [
                "DEPARTMENT_NAME",
                "PO_BOX_NUMBER",
                "SUB_BUILDING_NAME",
                "BUILDING_NAME",
                "BUILDING_NUMBER",
                "DEPENDENT_THOROUGHFARE",
                "THOROUGHFARE",
                "DOUBLE_DEPENDENT_LOCALITY",
                "DEPENDENT_LOCALITY",
                "POST_TOWN",
            ]
            kwargs = {k.lower(): line[k] for k in line if k in address_fields}
            kwargs["organisation_name"] = line["RM_ORGANISATION_NAME"]
            return PAFAddressFormatter(**kwargs).generate_address_label()
        address_fields = [
            "SAO_START_NUMBER",
            "SAO_START_SUFFIX",
            "SAO_END_NUMBER",
            "SAO_END_SUFFIX",
            "SAO_TEXT",
            "PAO_START_NUMBER",
            "PAO_START_SUFFIX",
            "PAO_END_NUMBER",
            "PAO_END_SUFFIX",
            "PAO_TEXT",
            "STREET_DESCRIPTION",
            "LOCALITY",
            "TOWN_NAME",
        ]
        kwargs = {k.lower(): line[k] for k in line if k in address_fields}
        kwargs["organisation_name"] = line["LA_ORGANISATION"]
        return LocalAuthAddressFormatter(**kwargs).generate_address_label()

    def clean_output_line(self, line):
        data = {}
        data["UPRN"] = line["UPRN"]
        data["address"] = self.clean_address(line)
        if line["ADDRESSBASE_POSTAL"] == "D":
            data["postcode"] = line["POSTCODE"]
        else:
            data["postcode"] = line["POSTCODE_LOCATOR"]
        data["location"] = "SRID=4326;POINT({} {})".format(
            line["LONGITUDE"], line["LATITUDE"]
        )
        data["addressbase_postal"] = line["ADDRESSBASE_POSTAL"]
        return data
