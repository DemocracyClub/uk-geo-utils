from django.contrib.gis.db import models

try:
    from django.contrib.gis.db.models.manager import GeoManager
except ImportError:
    from django.db.models import Manager as GeoManager


class CachedGetMixin:
    def get_cached(self, pk):
        for record in self:
            if record.pk == pk:
                return record
        raise self.model.DoesNotExist()


class AddressQuerySet(models.QuerySet, CachedGetMixin):
    @property
    def centroid(self):
        if not self:
            return None

        if len(self) == 1:
            return self[0].location

        base_point = self[0].location
        poly = base_point.union(self[1].location)
        for m in self:
            poly = poly.union(m.location)

        return poly.centroid


class AbstractAddressManager(GeoManager):
    def get_queryset(self):
        return AddressQuerySet(self.model, using=self._db)


class AbstractAddress(models.Model):
    uprn = models.CharField(primary_key=True, max_length=100)
    address = models.TextField(blank=True)
    postcode = models.CharField(blank=True, max_length=15, db_index=True)
    location = models.PointField(null=True, blank=True)
    addressbase_postal = models.CharField(blank=False, max_length=1)
    objects = AbstractAddressManager()

    class Meta:
        abstract = True


class Address(AbstractAddress):
    pass


class OnsudQuerySet(models.QuerySet, CachedGetMixin):
    pass


class AbstractOnsudManager(GeoManager):
    def get_queryset(self):
        return OnsudQuerySet(self.model, using=self._db)


class AbstractOnsud(models.Model):
    uprn = models.CharField(primary_key=True, max_length=12)
    cty = models.CharField(blank=True, max_length=9)
    ced = models.CharField(blank=True, max_length=9)
    lad = models.CharField(blank=True, max_length=9)
    ward = models.CharField(blank=True, max_length=9)
    parish = models.CharField(blank=True, max_length=9)
    hlthau = models.CharField(blank=True, max_length=9)
    ctry = models.CharField(blank=True, max_length=9)
    rgn = models.CharField(blank=True, max_length=9)
    pcon = models.CharField(blank=True, max_length=9)
    eer = models.CharField(blank=True, max_length=9)
    ttwa = models.CharField(blank=True, max_length=9)
    nuts = models.CharField(blank=True, max_length=9)
    park = models.CharField(blank=True, max_length=9)
    oa11 = models.CharField(blank=True, max_length=9)
    lsoa11 = models.CharField(blank=True, max_length=9)
    msoa11 = models.CharField(blank=True, max_length=9)
    wz11 = models.CharField(blank=True, max_length=9)
    ccg = models.CharField(blank=True, max_length=9)
    bua11 = models.CharField(blank=True, max_length=9)
    buasd11 = models.CharField(blank=True, max_length=9)
    ruc11 = models.CharField(blank=True, max_length=2)
    oac11 = models.CharField(blank=True, max_length=3)
    lep1 = models.CharField(blank=True, max_length=9)
    lep2 = models.CharField(blank=True, max_length=9)
    pfa = models.CharField(blank=True, max_length=9)
    imd = models.CharField(blank=True, max_length=5)
    objects = AbstractOnsudManager()

    def _get_oscty(self):
        return self.cty

    def _get_oslaua(self):
        return self.lad

    def _get_osward(self):
        return self.ward

    def _get_oshlthau(self):
        return self.hlthau

    def _get_ru11ind(self):
        return self.ruc11

    oscty = property(_get_oscty)
    oslaua = property(_get_oslaua)
    osward = property(_get_osward)
    oshlthau = property(_get_oshlthau)
    ru11ind = property(_get_ru11ind)

    class Meta:
        abstract = True


class Onsud(AbstractOnsud):
    pass


class AbstractOnspd(models.Model):
    pcd = models.CharField(blank=True, max_length=7)
    pcd2 = models.CharField(blank=True, max_length=8)
    pcds = models.CharField(blank=True, max_length=8, primary_key=True)
    dointr = models.CharField(blank=True, max_length=6)
    doterm = models.CharField(blank=True, max_length=6)
    oscty = models.CharField(blank=True, max_length=9)
    ced = models.CharField(blank=True, max_length=9)
    oslaua = models.CharField(blank=True, max_length=9)
    osward = models.CharField(blank=True, max_length=9)
    parish = models.CharField(blank=True, max_length=9)
    usertype = models.CharField(blank=True, max_length=1)
    oseast1m = models.CharField(blank=True, max_length=6)
    osnrth1m = models.CharField(blank=True, max_length=7)
    osgrdind = models.CharField(blank=True, max_length=1)
    oshlthau = models.CharField(blank=True, max_length=9)
    nhser = models.CharField(blank=True, max_length=9)
    ctry = models.CharField(blank=True, max_length=9)
    rgn = models.CharField(blank=True, max_length=9)
    streg = models.CharField(blank=True, max_length=1)
    pcon = models.CharField(blank=True, max_length=9)
    eer = models.CharField(blank=True, max_length=9)
    teclec = models.CharField(blank=True, max_length=9)
    ttwa = models.CharField(blank=True, max_length=9)
    pct = models.CharField(blank=True, max_length=9)
    itl = models.CharField(blank=True, max_length=10)
    statsward = models.CharField(blank=True, max_length=6)
    oa01 = models.CharField(blank=True, max_length=10)
    casward = models.CharField(blank=True, max_length=6)
    npark = models.CharField(blank=True, max_length=9)
    lsoa01 = models.CharField(blank=True, max_length=9)
    msoa01 = models.CharField(blank=True, max_length=9)
    ur01ind = models.CharField(blank=True, max_length=1)
    oac01 = models.CharField(blank=True, max_length=3)
    oa11 = models.CharField(blank=True, max_length=9)
    lsoa11 = models.CharField(blank=True, max_length=9)
    msoa11 = models.CharField(blank=True, max_length=9)
    wz11 = models.CharField(blank=True, max_length=9)
    bua24 = models.CharField(blank=True, max_length=9)
    ru11ind = models.CharField(blank=True, max_length=2)
    oac11 = models.CharField(blank=True, max_length=3)
    lat = models.CharField(blank=True, max_length=10)
    long = models.CharField(blank=True, max_length=10)
    lep1 = models.CharField(blank=True, max_length=9)
    lep2 = models.CharField(blank=True, max_length=9)
    pfa = models.CharField(blank=True, max_length=9)
    imd = models.CharField(blank=True, max_length=5)
    calncv = models.CharField(blank=True, max_length=9)
    oa21 = models.CharField(blank=True, max_length=9)
    lsoa21 = models.CharField(blank=True, max_length=9)
    msoa21 = models.CharField(blank=True, max_length=9)
    icb = models.CharField(blank=True, max_length=9)
    sicbl = models.CharField(blank=True, max_length=9)
    sicbl = models.CharField(blank=True, max_length=9)

    location = models.PointField(null=True, blank=True)
    objects = GeoManager()

    def _get_cty(self):
        """
        Note: these are not _exactly_ the same because

        'CTY' in ONSUD is:
        E10000002 - E10000034 = England (county);
        E11000001 - E11000007 = England (metropolitan county);
        E13000001 - E13000002 = England (Inner/Outer London);
        E99999999 (pseudo) = England (UA/MD/LB);
        W99999999 (pseudo) = Wales;
        S99999999 (pseudo) = Scotland

        whereas 'OSCTY' in ONSPD is
        E10000002 – E10000034 = England;
        E99999999 (pseudo) = England (UA/MD/LB);
        W99999999 (pseudo) = Wales;
        S99999999 (pseudo) = Scotland;
        """
        return self.oscty

    def _get_lad(self):
        return self.oslaua

    def _get_ward(self):
        return self.osward

    def _get_hlthau(self):
        return self.oshlthau

    def _get_ruc11(self):
        return self.ru11ind

    cty = property(_get_cty)
    lad = property(_get_lad)
    ward = property(_get_ward)
    hlthau = property(_get_hlthau)
    ruc11 = property(_get_ruc11)

    class Meta:
        abstract = True


class Onspd(AbstractOnspd):
    pass
