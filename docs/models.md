# Model Fields and Aliases

## Fields

### ONSUD

The [ONSUD model](https://github.com/DemocracyClub/uk-geo-utils/blob/17f7b175461057e6dfe0160acfc4ae7316157515/uk_geo_utils/models.py#L60-L88) provides a django model field for each field in the ONSUD.

See the ONSUD [release notes](https://www.arcgis.com/sharing/rest/content/items/64fbb8bb4ddc4acd8bce9489d87ec4fe/data) for the description of each field.

### ONSPD

The [ONSPD model](https://github.com/DemocracyClub/uk-geo-utils/blob/17f7b175461057e6dfe0160acfc4ae7316157515/uk_geo_utils/models.py#L99-L147) provides a django model field for each field in the ONSPD.

See the ONSPD [release notes](https://www.arcgis.com/sharing/rest/content/items/abff4f6fc0514c53bf02c9b9100d6523/data) for the description of each field.

## Aliases

Where comparable fields exist in the ONSUD and ONSPD with different names, there are some convenience aliases defined on the ONSPD model.
This means the ONSUD field name will work on the ONSPD model. 
The corresponding fields are listed in the table below.This allows us to reference comparable columns using a consistent name across models.

i.e. `Onspd.object.get(pk=1).wd25cd == Onspd.object.get(pk=1).ward`

| ONSPD      | ONSUD  |
|------------|--------|
| cty25cd    | cty    |
| lad25cd    | lad    |
| wd25cd     | ward   |
| hlth19cd   | hlthau |
| ruc11ind   | ruc11  |

There is also an alias for `usertype`. So `Onspd.object.get(pk=1).usertype == Onspd.object.get(pk=1).usertypeind`
