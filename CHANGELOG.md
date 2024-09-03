# Changelog

## :package: [0.13.0](https://pypi.org/project/uk-geo-utils/0.13.0/) - 2024-09-03

* Fix help text for `import_cleaned_addresses` command 
* Tested on Python 3.10/3.12, drop Python<3.10
* Tested on Django 4.2/5.1, drop Django<4.2
* Tested against Postgres 16

## :package: [0.12.0](https://pypi.org/project/uk-geo-utils/0.12.0/) - 2023-07-21

* Tested on Django 4.2

## :package: [0.11.0](https://pypi.org/project/uk-geo-utils/0.11.0/) - 2022-11-14

* Update ONSPD model for 2021 census fields. Now call with `--header may2018` or `--header aug2022`.
* Specify required python versions 3.8-3.10 inline with CI testing. 

## :package: [0.10.0](https://pypi.org/project/uk-geo-utils/0.10.0/) - 2020-08-25

* Fixed issue where ForeignKey relationships would return the relation not
 the code when using `get_code`.

## :package: [0.9.0](https://pypi.org/project/uk-geo-utils/0.9.0/) - 2019-02-06

* Add pre-processing script for Addressbase Plus: `clean_addressbase_plus`
* Rename pre-processing script for AddressBase Standard from `clean_addressbase` to `clean_addressbase_standard`
* Add `addressbase_postal` field to `AbstractAddress` and `Address` model
* Only use type D UPRNs for calculating `.centroid` in `AddressBaseGeocoder`

## :package: [0.8.1](https://pypi.org/project/uk-geo-utils/0.8.1/) - 2019-10-16

Tested on Python 3.8

## :package: [0.8.0](https://pypi.org/project/uk-geo-utils/0.8.0/) - 2019-06-03

* Add support for django 2.1, 2.2
* Drop support for django 2.0

## :package: [0.7.0](https://pypi.org/project/uk-geo-utils/0.7.0/) - 2019-02-15

* Tested on python 3.7
* Update for Jan 2019 ONSUD format change (ctry_flag column is removed)
* Fix `ResourceWarning`s

## :package: [0.6.0](https://pypi.org/project/uk-geo-utils/0.6.0/) - 2018-09-14

Add optional `--transaction` flag to `import_` commands

## :package: [0.5.0](https://pypi.org/project/uk-geo-utils/0.5.0/) - 2018-06-16

Add support for Django 2.0

## :package: [0.4.0](https://pypi.org/project/uk-geo-utils/0.4.0/) - 2018-06-12

Update for May 2018 ONSPD format changes

## :package: [0.3.0](https://pypi.org/project/uk-geo-utils/0.3.0/) - 2018-05-22

* Ensure we always throw error if no CSV files found to import
* Check for files before clearing old data in import scripts
* Throw `OnsudNotImportedException` and `OnspdNotImportedException`
* Expose `uprns` and `addresses` as properties in `AddressBaseGeocoder`
* Add field aliases to ONSUD model
* Add Documentation
* Distribute via PyPI

## :package: 0.2.0 - 2018-03-05

Update for Feb 2018 ONSUD format changes

## :package: 0.1.0 - 2018-03-05

First Release
