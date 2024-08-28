from django.test import TestCase

from uk_geo_utils.helpers import LocalAuthAddressFormatter


class LocalAuthAddressFormatterTest(TestCase):
    def test_pao_x_to_y(self):
        af = LocalAuthAddressFormatter(
            organisation_name="TESCO STORES LTD",
            sao_start_number="",
            sao_start_suffix="",
            sao_end_number="",
            sao_end_suffix="",
            sao_text="",
            pao_start_number="138",
            pao_start_suffix="",
            pao_end_number="142",
            pao_end_suffix="",
            pao_text="",
            street_description="CHELTENHAM ROAD",
            locality="MONTPELIER",
            town_name="BRISTOL",
        )
        self.assertEqual(
            "TESCO STORES LTD, 138-142 CHELTENHAM ROAD, MONTPELIER, BRISTOL",
            af.generate_address_label(),
        )

    def test_pao_with_suffixes(self):
        af = LocalAuthAddressFormatter(
            organisation_name="",
            sao_start_number="",
            sao_start_suffix="",
            sao_end_number="",
            sao_end_suffix="",
            sao_text="",
            pao_start_number="1",
            pao_start_suffix="C",
            pao_end_number="1",
            pao_end_suffix="D",
            pao_text="",
            street_description="CHANDOS ROAD",
            locality="REDLAND",
            town_name="BRISTOL",
        )
        self.assertEqual(
            "1C-1D CHANDOS ROAD, REDLAND, BRISTOL", af.generate_address_label()
        )

    def test_pao_with_text(self):
        af = LocalAuthAddressFormatter(
            organisation_name="",
            sao_start_number="",
            sao_start_suffix="",
            sao_end_number="",
            sao_end_suffix="",
            sao_text="",
            pao_start_number="9",
            pao_start_suffix="",
            pao_end_number="",
            pao_end_suffix="",
            pao_text="HIGHGATE HOUSE",
            street_description="UPPER BELGRAVE ROAD",
            locality="CLIFTON",
            town_name="BRISTOL",
        )
        self.assertEqual(
            "HIGHGATE HOUSE 9 UPPER BELGRAVE ROAD, CLIFTON, BRISTOL",
            af.generate_address_label(),
        )

    def test_pao_and_sao_number(self):
        af = LocalAuthAddressFormatter(
            organisation_name="",
            sao_start_number="3",
            sao_start_suffix="A",
            sao_end_number="",
            sao_end_suffix="",
            sao_text="",
            pao_start_number="",
            pao_start_suffix="",
            pao_end_number="",
            pao_end_suffix="",
            pao_text="COTHAM PARK MANSIONS",
            street_description="COTHAM PARK NORTH",
            locality="COTHAM",
            town_name="BRISTOL",
        )
        self.assertEqual(
            "3A COTHAM PARK MANSIONS COTHAM PARK NORTH, COTHAM, BRISTOL",
            af.generate_address_label(),
        )

    def test_pao_and_sao_text(self):
        af = LocalAuthAddressFormatter(
            organisation_name="",
            sao_start_number="",
            sao_start_suffix="",
            sao_end_number="",
            sao_end_suffix="",
            sao_text="FLAT 1",
            pao_start_number="4",
            pao_start_suffix="A",
            pao_end_number="",
            pao_end_suffix="",
            pao_text="",
            street_description="WARWICK ROAD",
            locality="COTHAM",
            town_name="BRISTOL",
        )
        self.assertEqual(
            "FLAT 1 4A WARWICK ROAD, COTHAM, BRISTOL",
            af.generate_address_label(),
        )
