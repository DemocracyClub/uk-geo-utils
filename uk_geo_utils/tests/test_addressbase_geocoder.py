from django.contrib.gis.geos import Point
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase

from uk_geo_utils.geocoders import (
    AddressBaseGeocoder,
    AddressBaseNotImportedException,
    CodesNotFoundException,
    MultipleCodesException,
    NorthernIrelandException,
    OnsudNotImportedException,
    StrictMatchException,
    get_address_model,
    get_onsud_model,
)
from uk_geo_utils.helpers import AddressSorter
from uk_geo_utils.models import Address


class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)


class AddressBaseGeocoderTest(TestCase):
    fixtures = [
        # records in Address, no corresponding records in ONSUD
        "addressbase_geocoder/AA11AA.json",
        # 3 records in Address, 2 corresponding records in ONSUD
        # all in county A01000001 and local auth B01000001
        "addressbase_geocoder/BB11BB.json",
        # records in Address, corresponding records in ONSUD
        # all in county A01000001 but split across
        # local auths B01000001 and B01000002
        "addressbase_geocoder/CC11CC.json",
    ]

    def test_empty_addressbase_table(self):
        """
        The AddressBase table has no records in it
        """
        get_address_model().objects.all().delete()
        with self.assertNumQueries(FuzzyInt(0, 4)), self.assertRaises(
            AddressBaseNotImportedException
        ):
            AddressBaseGeocoder("AA11AA")

    def test_empty_onsud_table(self):
        """
        The ONSUD table has no records in it
        """
        get_onsud_model().objects.all().delete()
        with self.assertNumQueries(FuzzyInt(0, 4)), self.assertRaises(
            OnsudNotImportedException
        ):
            AddressBaseGeocoder("AA11AA")

    def test_northern_ireland(self):
        with self.assertNumQueries(FuzzyInt(0, 4)), self.assertRaises(
            NorthernIrelandException
        ):
            AddressBaseGeocoder("BT11AA")

    def test_no_records(self):
        """
        We can't find any records for the given postcode in the AddressBase table
        """
        with self.assertNumQueries(FuzzyInt(0, 4)), self.assertRaises(
            get_address_model().DoesNotExist
        ):
            AddressBaseGeocoder("ZZ1 1ZZ")

    def test_no_codes(self):
        """
        We find records for the given postcode in the AddressBase table
        but there are no corresponding records in the ONSUD for the UPRNs we found
        """
        with self.assertNumQueries(FuzzyInt(0, 5)):
            addressbase = AddressBaseGeocoder("AA11AA")

            with self.assertRaises(CodesNotFoundException):
                addressbase.get_code("lad")

            self.assertIsInstance(addressbase.centroid, Point)

    def test_valid(self):
        """
        We find records for the given postcode in the AddressBase table
        There are some corresponding records in the ONSUD for the UPRNs we found

        Valid result should be returned

        Note that in this case, the ONSUD table does not contain corresponding
        records for *all* of the UPRNs we found, but we accept the result anyway
        """
        with self.assertNumQueries(FuzzyInt(0, 5)):
            addressbase = AddressBaseGeocoder(
                "bb 1   1B B"
            )  # intentionally spurious whitespace and case
            self.assertEqual("B01000001", addressbase.get_code("lad"))
            self.assertIsInstance(addressbase.centroid, Point)

    def test_strict_mode(self):
        """
        We find records for the given postcode in the AddressBase table
        There are some corresponding records in the ONSUD for the UPRNs we found

        Note that in this case, the ONSUD table does not contain corresponding
        records for *all* of the UPRNs we found, and we are passing strict=True
        so we raise a StrictMatchException
        """
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("BB11BB")
            with self.assertRaises(StrictMatchException):
                addressbase.get_code("lad", strict=True)

    def test_multiple_codes(self):
        """
        We find records for the given postcode in the AddressBase table
        There are corresponding records in the ONSUD for the UPRNs we found
        The UPRNs described by this postcode map to more than one 'lad'
        but they all map to the same 'cty'
        """
        with self.assertNumQueries(FuzzyInt(0, 5)):
            addressbase = AddressBaseGeocoder("CC1 1CC")

            with self.assertRaises(MultipleCodesException):
                addressbase.get_code("lad")

            self.assertEqual("A01000001", addressbase.get_code("cty"))

            self.assertIsInstance(addressbase.centroid, Point)

    def test_invalid_code_type(self):
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("CC1 1CC")
            with self.assertRaises(FieldDoesNotExist):
                addressbase.get_code("foo")  # not a real code type

    def test_get_code_by_uprn_valid(self):
        """
        valid get_code() by UPRN queries
        """
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("CC1 1CC")
            self.assertEqual(
                "B01000001", addressbase.get_code("lad", "00000008")
            )
            self.assertIsInstance(addressbase.get_point("00000008"), Point)
            self.assertEqual(
                "B01000002", addressbase.get_code("lad", "00000009")
            )
            self.assertIsInstance(addressbase.get_point("00000009"), Point)

    def test_get_code_by_uprn_invalid_uprn(self):
        """
        'foo' is not a valid UPRN in our DB
        """
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("CC1 1CC")
            with self.assertRaises(get_address_model().DoesNotExist):
                addressbase.get_code("lad", "foo")
            with self.assertRaises(get_address_model().DoesNotExist):
                addressbase.get_point("foo")

    def test_get_code_by_uprn_invalid_uprn_for_postcode(self):
        """
        '00000001' is a valid UPRN in our DB,
        but for a different postcode
        than the one we constructed with
        """
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("CC1 1CC")
            with self.assertRaises(get_address_model().DoesNotExist):
                addressbase.get_code("lad", "00000001")
            with self.assertRaises(get_address_model().DoesNotExist):
                addressbase.get_point("00000001")

    def test_get_code_by_uprn_no_onsud(self):
        """
        '00000006' is a valid UPRN in AddressBase but not in ONSUD
        """
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("BB1 1BB")
            with self.assertRaises(get_onsud_model().DoesNotExist):
                addressbase.get_code("lad", "00000006")
            self.assertIsInstance(addressbase.get_point("00000006"), Point)

    def test_addresses_property(self):
        with self.assertNumQueries(FuzzyInt(0, 4)):
            addressbase = AddressBaseGeocoder("AA1 1AA")
            addressbase._addresses = addressbase._addresses.order_by("-address")
            self.assertNotEqual(addressbase._addresses, addressbase.addresses)
            sorter = AddressSorter(addressbase._addresses)
            self.assertEqual(addressbase.addresses, sorter.natural_sort())

    def test_centroid_ignores_type_l(self):
        addressbase = AddressBaseGeocoder("BB11BB")
        before_centroid = addressbase.centroid
        # adding a type L UPRN shouldn't change the postcode centroid
        Address.objects.create(
            postcode="BB1 1BB",
            address="foobar",
            location=Point(94.5, 65.7, srid=4326),
            addressbase_postal="L",
        )
        after_centroid = addressbase.centroid
        self.assertEqual(before_centroid, after_centroid)
