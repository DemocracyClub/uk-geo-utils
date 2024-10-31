# Importing Data

`django-uk-geo-utils` is most useful for users of AddressBase. Unfortunately AddressBase is proprietary data so it isn't accessible to everyone. If you have a licence for AddressBase or access via the [PSGA](https://www.ordnancesurvey.co.uk/customers/public-sector/public-sector-geospatial-agreement), import AddressBase Standard, ONSUD and ONSPD. If you don't have access to AddressBase, skip straight to ONSPD. You don't need ONSUD.

## AddressBase

Ordnance Survey AddressBase contains UPRNs (Unique Property Reference Number), addresses, and grid references for UK properties. Order a copy of AddressBase and download from the Ordnance Survey website/FTP. The import is done in 2 stages:

* First we need to do some pre-processing on the data.
    * For AddressBase Standard: `python manage.py clean_addressbase_standard /path/to/data`
    * For AddressBase Plus: `python manage.py clean_addressbase_plus /path/to/data`
* Then the processed files can be imported: `python manage.py import_cleaned_addresses /path/to/data`


## ONSUD

ONS UPRN Directory is the companion dataset to AddressBase and handles mapping UPRNs to a variety of administrative, electoral, and statistical geographies. Grab the latest release from the [Office for National Statistics](https://ons.maps.arcgis.com/home/search.html?t=content&q=tags%3AONS%20UPRN%20Directory&start=1&sortOrder=desc&sortField=modified), extract and import it:

`python manage.py import_onsud /path/to/data`

## ONSPD

ONS Postcode Directory maps postcodes to grid references and a variety of administrative, electoral, and statistical geographies. Grab the latest release from the [Office for National Statistics](https://ons.maps.arcgis.com/home/search.html?t=content&q=tags%3AONS%20Postcode%20Directory&start=1&sortOrder=desc&sortField=modified), extract and import it:

`python manage.py import_onspd /path/to/data`

# Custom Importers

You can implement a new importer by extending the [BaseImporter](https://github.com/DemocracyClub/uk-geo-utils/blob/master/uk_geo_utils/base_importer.py) class and implementing a custom `import_data_to_temp_table` method. 
The pattern that the `BaseImporter` class implements is to create a temp table and use `COPY` to write data to the temp table, it then reproduces the indexes from the original table on the temp table. Finally, within a transaction, the original table is dropped and the temporary table, it's indexes and contraints are renamed to replace the original.
The reason for this is it's much, much quicker
You can look at [import_onspd](https://github.com/DemocracyClub/uk-geo-utils/blob/master/uk_geo_utils/management/commands/import_onspd.py) or [import_cleaned_addresses](https://github.com/DemocracyClub/uk-geo-utils/blob/master/uk_geo_utils/management/commands/import_cleaned_addresses.py) for prior art.
