# mepram-api Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0dev] - 2026-05-20 : <https://github.com/Aberdur/mepram-api/releases/tag/v0.1.0dev>

### Credits

- [Alejandro Bernabeu](https://github.com/aberdur)
- [Enrique Sapena](https://github.com/ESapenaVentura)

#### Added enhancements

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

#### Changed

- Align database implementation with PathoCore API by using MySQL, Django ORM models and migrations instead of querying an unmanaged external schema [#1](https://github.com/Aberdur/mepram-api/pull/1)

#### Removed

### Requirements
