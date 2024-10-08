import abc

from django.core.exceptions import ObjectDoesNotExist

from uk_geo_utils.helpers import (
    AddressSorter,
    Postcode,
    get_address_model,
    get_onspd_model,
    get_onsud_model,
)


class AddressBaseException(Exception):
    pass


class CodesNotFoundException(AddressBaseException):
    pass


class MultipleCodesException(AddressBaseException):
    pass


class StrictMatchException(AddressBaseException):
    pass


class NorthernIrelandException(ObjectDoesNotExist):
    pass


class AddressBaseNotImportedException(ObjectDoesNotExist):
    pass


class OnsudNotImportedException(ObjectDoesNotExist):
    pass


class OnspdNotImportedException(ObjectDoesNotExist):
    pass


class BaseGeocoder(metaclass=abc.ABCMeta):
    def __init__(self, postcode):
        self.postcode = Postcode(postcode)

    @property
    @abc.abstractmethod
    def centroid(self):
        pass

    @abc.abstractmethod
    def get_code(code_type, uprn=None):
        pass


class AddressBaseGeocoder(BaseGeocoder):
    def __init__(self, postcode):
        self.postcode = Postcode(postcode)
        if self.postcode.territory == "NI":
            raise NorthernIrelandException("Postcode is in Northern Ireland")

        self.onsud_model = get_onsud_model()
        self.address_model = get_address_model()

        # check the data we need exists
        if not self.address_model.objects.all().exists():
            raise AddressBaseNotImportedException("Address Base table is empty")
        if not self.onsud_model.objects.all().exists():
            raise OnsudNotImportedException("ONSUD table is empty")

        self._addresses = self.address_model.objects.filter(
            postcode=self.postcode.with_space
        ).order_by("uprn")
        if not self._addresses:
            raise self.address_model.DoesNotExist(
                "No addresses found for postcode %s" % (self.postcode)
            )

        self._uprns = self.onsud_model.objects.filter(
            uprn__in=self.uprns
        ).order_by("uprn")

    @property
    def uprns(self):
        return [a.uprn for a in self._addresses]

    @property
    def centroid(self):
        type_d_addresses = self._addresses.filter(addressbase_postal="D")
        if len(type_d_addresses) > 0:
            return type_d_addresses.centroid
        return self._addresses.centroid

    @property
    def addresses(self):
        sorter = AddressSorter(self._addresses)
        return sorter.natural_sort()

    def get_point(self, uprn):
        return self._addresses.get_cached(uprn).location

    def get_code(self, code_type, uprn=None, strict=False):
        # check the code_type field exists on our model
        code_type_field = self.onsud_model._meta.get_field(code_type)

        if uprn:
            self._addresses.get_cached(uprn)
            return getattr(self._uprns.get_cached(uprn), code_type)

        if len(self._uprns) == 0:
            # No records in the ONSUD table were found for the given UPRNs
            # because...reasons
            raise CodesNotFoundException(
                "Found no records in ONSUD for supplied UPRNs"
            )
        if len(self._addresses) != len(self._uprns):
            if strict:
                for uprn in self.uprns:
                    try:
                        self._uprns.get_cached(uprn)
                    except self.onsud_model.DoesNotExist:
                        raise StrictMatchException(
                            "expected UPRN %s not found in ONSUD" % uprn
                        )
            else:
                # if not strict, ignore this condition
                pass

        codes = {getattr(u, code_type_field.attname) for u in self._uprns}
        if len(codes) == 1:
            # all the uprns supplied are in the same area
            return list(codes)[0]
        raise MultipleCodesException(
            "Postcode %s covers UPRNs in more than one '%s' area"
            % (self.postcode, code_type)
        )


class OnspdGeocoder(BaseGeocoder):
    def __init__(self, postcode):
        self.postcode = Postcode(postcode)
        self.onspd_model = get_onspd_model()

        if not self.onspd_model.objects.all().exists():
            raise OnspdNotImportedException("ONSPD table is empty")

        self.record = self.onspd_model.objects.get(
            pcds=self.postcode.with_space, doterm=""
        )

    @property
    def centroid(self):
        return self.record.location

    def get_code(self, code_type):
        return getattr(self.record, code_type)
