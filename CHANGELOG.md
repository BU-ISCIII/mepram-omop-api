# mepram-api Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-07-02 : <https://github.com/BU-ISCIII/mepram-omop-api/releases/tag/1.0.1>

### Credits

- [Alejandro Bernabeu](https://github.com/aberdur)
- [Enrique Sapena](https://github.com/ESapenaVentura)

#### Added enhancements

- Added protected POST endpoint for reports [#15](https://github.com/BU-ISCIII/mepram-omop-api/pull/15)

#### Fixes

- Fixed missing files in release 1.0.0

#### Changed

#### Removed

### Requirements

## [1.0.0] - 2026-07-02 : <https://github.com/BU-ISCIII/mepram-omop-api/releases/tag/1.0.0>

### Credits

- [Alejandro Bernabeu](https://github.com/aberdur)
- [Enrique Sapena](https://github.com/ESapenaVentura)

#### Added enhancements

- Add new endpoint for pre-generated reports and surfaced total_medical_concepts in metadata endpoint [#11](https://github.com/BU-ISCIII/mepram-omop-api/pull/11)
- Add default throttle at 500 requests/hour and set authentication as "false" by default [#9](https://github.com/BU-ISCIII/mepram-omop-api/pull/9)
- Add configurable Django superuser bootstrap for local/test Swagger and admin access [#7](https://github.com/BU-ISCIII/mepram-omop-api/pull/7)
- Add installation scripts that emulate Iskylim's approach [#2](https://github.com/BU-ISCIII/mepram-omop-api/pull/2)
- Add Django/DRF MVP API for read-only access to the aggregated OMOP dashboard schema [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add Docker test stack with MySQL, following the PathoCore API local stack pattern [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add OpenAPI and Swagger documentation with `drf-spectacular` [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add endpoints for health, metadata, capabilities, cohort summary, domains, concepts, concept facts and measurements [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add Django-managed dashboard models and initial migrations for the MePRAM API schema [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add a management command to import PostgreSQL `dashboard.sql` COPY data into the Django-managed MySQL schema [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add support for age, sex and age+sex stratifications where available in `dashboard.sql` [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add local CORS configuration for PathoCore Web integration [#1](https://github.com/Aberdur/mepram-api/pull/1)
- Add README installation and local test stack documentation [#1](https://github.com/Aberdur/mepram-api/pull/1)

#### Fixes

- Fixed installation location to point to /srv and test ports to point to 8000/3000 [#3](https://github.com/BU-ISCIII/mepram-omop-api/pull/3)
- Fixed README to remove Keycloak and other security aspects [#14](https://github.com/BU-ISCIII/mepram-omop-api/pull/14)


#### Changed

- Align database implementation with PathoCore API by using MySQL, Django ORM models and migrations instead of querying an unmanaged external schema [#1](https://github.com/Aberdur/mepram-api/pull/1)

#### Removed

### Requirements
