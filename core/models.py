from django.db import models


class DashboardModel(models.Model):
    class Meta:
        abstract = True


class DimPatient(DashboardModel):
    person_id = models.DecimalField(max_digits=30, decimal_places=0, primary_key=True)
    gender_concept_id = models.DecimalField(max_digits=30, decimal_places=0, null=True)
    gender = models.CharField(max_length=255, null=True)
    birth_date = models.DateField(null=True)
    reference_date = models.DateField(null=True)
    age_at_reference = models.DecimalField(max_digits=30, decimal_places=10, null=True)
    age_group = models.CharField(max_length=255, null=True)

    class Meta(DashboardModel.Meta):
        db_table = "dim_patient"


class Concept(DashboardModel):
    concept_id = models.DecimalField(max_digits=30, decimal_places=0, primary_key=True)
    concept_name = models.CharField(max_length=255, null=True)
    domain_id = models.CharField(max_length=255, null=True)
    vocabulary_id = models.CharField(max_length=255, null=True)
    concept_code = models.CharField(max_length=255, null=True)

    class Meta(DashboardModel.Meta):
        db_table = "concepts"


class EventsLong(DashboardModel):
    person_id = models.IntegerField(null=True)
    concept_id = models.IntegerField(null=True)
    domain_id = models.CharField(max_length=255, null=True)
    event_type = models.CharField(max_length=255, null=True)
    source_domain_id = models.CharField(max_length=255, null=True)

    class Meta(DashboardModel.Meta):
        db_table = "events_long"


class FactDomain(DashboardModel):
    domain_id = models.CharField(max_length=255, primary_key=True)
    medical_concepts = models.IntegerField(null=True)
    participants = models.IntegerField(null=True)

    class Meta(DashboardModel.Meta):
        db_table = "fact_domain"


class FactConceptBase(DashboardModel):
    concept_id = models.DecimalField(max_digits=30, decimal_places=0)
    concept_name = models.CharField(max_length=255, null=True)
    domain_id = models.CharField(max_length=255, null=True)
    vocabulary_id = models.CharField(max_length=255, null=True)
    concept_code = models.CharField(max_length=255, null=True)
    event_type = models.CharField(max_length=255)
    patient_count = models.IntegerField(null=True)

    class Meta:
        abstract = True


class FactConcept(FactConceptBase):
    record_count = models.IntegerField(null=True)
    record_pct_overall = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(FactConceptBase.Meta):
        db_table = "fact_concept"


class FactConceptByAge(FactConceptBase):
    age_group = models.CharField(max_length=255)
    patient_pct_group = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct_concept = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(FactConceptBase.Meta):
        db_table = "fact_concept_by_age"


class FactConceptBySex(FactConceptBase):
    gender = models.CharField(max_length=255)
    patient_pct_group = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct_concept = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(FactConceptBase.Meta):
        db_table = "fact_concept_by_sex"


class FactConceptByAgeSex(FactConceptBase):
    age_group = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    patient_pct_group = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct_concept = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(FactConceptBase.Meta):
        db_table = "fact_concept_by_age_sex"


class NumericMeasurementBase(DashboardModel):
    concept_id = models.DecimalField(max_digits=30, decimal_places=0)
    concept_name = models.CharField(max_length=255, null=True)
    vocabulary_id = models.CharField(max_length=255, null=True)
    concept_code = models.CharField(max_length=255, null=True)
    event_type = models.CharField(max_length=255)
    unit_concept_id = models.DecimalField(max_digits=30, decimal_places=0)
    unit_name = models.CharField(max_length=255, null=True)
    n_records = models.IntegerField(null=True)
    n_patients = models.IntegerField(null=True)
    mean_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    sd_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    min_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    q1_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    median_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    q3_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    max_value = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta:
        abstract = True


class FactMeasurementNumeric(NumericMeasurementBase):
    class Meta(NumericMeasurementBase.Meta):
        db_table = "fact_measurement_numeric"


class FactMeasurementNumericByAge(NumericMeasurementBase):
    age_group = models.CharField(max_length=255)

    class Meta(NumericMeasurementBase.Meta):
        db_table = "fact_measurement_numeric_by_age"


class FactMeasurementNumericBySex(NumericMeasurementBase):
    gender = models.CharField(max_length=255)

    class Meta(NumericMeasurementBase.Meta):
        db_table = "fact_measurement_numeric_by_sex"


class FactMeasurementNumericByAgeSex(NumericMeasurementBase):
    age_group = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)

    class Meta(NumericMeasurementBase.Meta):
        db_table = "fact_measurement_numeric_by_age_sex"


class CategoricalMeasurementBase(DashboardModel):
    concept_id = models.DecimalField(max_digits=30, decimal_places=0)
    concept_name = models.CharField(max_length=255, null=True)
    vocabulary_id = models.CharField(max_length=255, null=True)
    concept_code = models.CharField(max_length=255, null=True)
    event_type = models.CharField(max_length=255)
    value_as_concept_id = models.DecimalField(max_digits=30, decimal_places=0)
    value_concept_name = models.CharField(max_length=255, null=True)
    record_count = models.IntegerField(null=True)
    patient_count = models.IntegerField(null=True)

    class Meta:
        abstract = True


class FactMeasurementCategorical(CategoricalMeasurementBase):
    patient_pct = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(CategoricalMeasurementBase.Meta):
        db_table = "fact_measurement_categorical"


class FactMeasurementCategoricalByAge(CategoricalMeasurementBase):
    age_group = models.CharField(max_length=255)
    patient_pct_group = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct_concept = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(CategoricalMeasurementBase.Meta):
        db_table = "fact_measurement_categorical_by_age"


class FactMeasurementCategoricalBySex(CategoricalMeasurementBase):
    gender = models.CharField(max_length=255)
    patient_pct_group = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct_concept = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(CategoricalMeasurementBase.Meta):
        db_table = "fact_measurement_categorical_by_sex"


class FactMeasurementCategoricalByAgeSex(CategoricalMeasurementBase):
    age_group = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    patient_pct_group = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    patient_pct_concept = models.DecimalField(max_digits=30, decimal_places=15, null=True)

    class Meta(CategoricalMeasurementBase.Meta):
        db_table = "fact_measurement_categorical_by_age_sex"
