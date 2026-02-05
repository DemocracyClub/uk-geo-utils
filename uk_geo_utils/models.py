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
    pcd7 = models.CharField(
        blank=True,
        max_length=7,
        help_text="Unit postcode – 7 character version",
    )
    pcd8 = models.CharField(
        blank=True,
        max_length=8,
        help_text="Unit postcode – 8 character version",
    )
    pcds = models.CharField(
        blank=True,
        max_length=8,
        primary_key=True,
        help_text="Unit postcode - variable length (e-Gif) version",
    )
    dointr = models.CharField(
        blank=True, max_length=6, help_text="Date of introduction"
    )
    doterm = models.CharField(
        blank=True, max_length=6, help_text="Date of termination"
    )
    cty25cd = models.CharField(blank=True, max_length=9, help_text="County")
    ced25cd = models.CharField(
        blank=True, max_length=9, help_text="County Electoral Division"
    )
    lad25cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Local authority district (LAD): unitary authority (UA)/non- metroploitan district (NMD)/metropolitan district (MD)/London borough (LB)/council area (CA)/district council area (DCA)",
    )
    wd25cd = models.CharField(
        blank=True, max_length=9, help_text="(Electoral) ward/division"
    )
    parncp25cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Civil parish/non-civil parish/community",
    )
    usrtypind = models.CharField(
        blank=True, max_length=1, help_text="Postcode user type"
    )
    east1m = models.CharField(
        blank=True, max_length=6, help_text="National grid reference - Easting"
    )
    north1m = models.CharField(
        blank=True, max_length=7, help_text="National grid reference - Northing"
    )
    gridind = models.CharField(
        blank=True,
        max_length=1,
        help_text="Grid reference positional quality indicator",
    )
    hlth19cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Former Strategic Health Authority (SHA)/Local Health Board (LHB)/Health Board (HB)/Health Authority (HA)/Health & Social Care Board (HSCB)",
    )
    nhser24cd = models.CharField(
        blank=True, max_length=9, help_text="NHS England (Region) (NHS ER)"
    )
    ctry25cd = models.CharField(blank=True, max_length=9, help_text="Country")
    rgn25cd = models.CharField(
        blank=True, max_length=9, help_text="Region (former GOR)"
    )
    ssr95cd = models.CharField(
        blank=True, max_length=9, help_text="Standard Statistical Region (SSR)"
    )
    pcon24cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Westminster parliamentary constituency",
    )
    eer20cd = models.CharField(
        blank=True, max_length=9, help_text="European Electoral Region"
    )
    educ23cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Local Learning and Skills Council (LLSC)/Dept. of Children, Education, Lifelong Learning and Skills (DCELLS)/Enterprise Region (ER)",
    )
    ttwa15cd = models.CharField(
        blank=True, max_length=9, help_text="Travel to Work Area (TTWA)"
    )
    pco19cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Primary Care Organisatioin (PCO): Care Trust (PCT)/Care Trust/Care Trust Plus (CT)/Local Health Board (LHB)/Community Health Partnership (CHP)/Local Commissioning Group (LCG)/Primary Healthcare Directorate (PHD)",
    )
    itl25cd = models.CharField(
        blank=True,
        max_length=10,
        help_text="International Territorial Level (former NUTS)",
    )
    wdstl05cd = models.CharField(
        blank=True,
        max_length=6,
        help_text="2005 ‘statistical’ ward (England and Wales only)",
    )
    oa01cd = models.CharField(
        blank=True, max_length=10, help_text="2001 Census Output Area (OA)"
    )
    wdcas03cd = models.CharField(
        blank=True, max_length=6, help_text="Census Area Statistics (CAS) ward"
    )
    npark16cd = models.CharField(
        blank=True, max_length=9, help_text="National park"
    )
    lsoa01cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2001 Census Lower Layer Super Output Area (LSOA)/Data Zone (DZ)/Super Output Area (SOA)",
    )
    msoa01cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2001 Census Middle Layer Super Output Area (MSOA)/Intermediate Zone (IZ)",
    )
    ruc01ind = models.CharField(
        blank=True, max_length=1, help_text="2001 Census urban/rural indicator"
    )
    oac01ind = models.CharField(
        blank=True,
        max_length=3,
        help_text=" 2001 Census Output Area classification (OAC)",
    )
    oa11cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2011 Census Output Area (OA)/Small Area (SA)",
    )
    lsoa11cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2011 Census Lower Layer Super Output Area (LSOA)/Data Zone (DZ)/SOA",
    )
    msoa11cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2011 Census Middle Layer Super Output Area (MSOA)/Intermediate Zone (IZ)",
    )
    wz11cd = models.CharField(
        blank=True, max_length=9, help_text="2011 Census Workplace Zone (WZ)"
    )
    bua24cd = models.CharField(
        blank=True, max_length=9, help_text="Built-up Area (BUA)"
    )
    ruc11ind = models.CharField(
        blank=True,
        max_length=2,
        help_text="2011 Census rural-urban classification",
    )
    oac11ind = models.CharField(
        blank=True,
        max_length=3,
        help_text="2011 Census Output Area classification (OAC)",
    )
    lat = models.CharField(
        blank=True, max_length=10, help_text="Decimal degrees latitude"
    )
    long = models.CharField(
        blank=True, max_length=10, help_text="Decimal degrees longitude"
    )
    lep21cd1 = models.CharField(
        blank=True,
        max_length=9,
        help_text="Local Enterprise Partnership (LEP) - first instance",
    )
    lep21cd2 = models.CharField(
        blank=True,
        max_length=9,
        help_text="Local Enterprise Partnership (LEP) - second instance",
    )
    pfa23cd = models.CharField(
        blank=True, max_length=9, help_text="Police Force Area (PFA)"
    )
    imd20ind = models.CharField(
        blank=True,
        max_length=5,
        help_text="Index of Multiple Deprivation (IMD)for 2011 LSOAs",
    )
    cal24cd = models.CharField(
        blank=True, max_length=9, help_text="Cancer Alliance (CAL)"
    )
    oa21cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2021 Census Output Area (OA)/Data Zone (DZ)",
    )
    lsoa21cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2021 Census Lower Layer Super Output Area (LSOA)/Super Data Zone (SDZ)",
    )
    msoa21cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="2021 Census Middle Layer Super Output Area (MSOA)",
    )
    ruc21ind = models.CharField(
        blank=True,
        max_length=4,
        help_text="2021 Census rural-urban classification",
    )
    icb23cd = models.CharField(
        blank=True, max_length=9, help_text="Integrated Care Board (ICB)"
    )
    sicbl24cd = models.CharField(
        blank=True,
        max_length=9,
        help_text="Sub ICB Location (LOC)/Local Health Board (LHB)/Community Health Partnership (CHP)/Local Commissioning Group (LCG)/Primary Healthcare Directorate (PHD)",
    )

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
        return self.cty25cd

    def _get_lad(self):
        return self.lad25cd

    def _get_ward(self):
        return self.wd25cd

    def _get_hlthau(self):
        return self.hlth19cd

    def _get_ruc11(self):
        return self.ruc11ind

    cty = property(_get_cty)
    lad = property(_get_lad)
    ward = property(_get_ward)
    hlthau = property(_get_hlthau)
    ruc11 = property(_get_ruc11)

    class Meta:
        abstract = True


class Onspd(AbstractOnspd):
    pass
