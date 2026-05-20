from core import models


FACT_CONCEPT_MODELS = {
    "none": models.FactConcept,
    "age": models.FactConceptByAge,
    "sex": models.FactConceptBySex,
    "age_sex": models.FactConceptByAgeSex,
}

NUMERIC_MEASUREMENT_MODELS = {
    "none": models.FactMeasurementNumeric,
    "age": models.FactMeasurementNumericByAge,
    "sex": models.FactMeasurementNumericBySex,
    "age_sex": models.FactMeasurementNumericByAgeSex,
}

CATEGORICAL_MEASUREMENT_MODELS = {
    "none": models.FactMeasurementCategorical,
    "age": models.FactMeasurementCategoricalByAge,
    "sex": models.FactMeasurementCategoricalBySex,
    "age_sex": models.FactMeasurementCategoricalByAgeSex,
}

DASHBOARD_MODELS = [
    models.DimPatient,
    models.Concept,
    models.EventsLong,
    models.FactDomain,
    models.FactConcept,
    models.FactConceptByAge,
    models.FactConceptBySex,
    models.FactConceptByAgeSex,
    models.FactMeasurementNumeric,
    models.FactMeasurementNumericByAge,
    models.FactMeasurementNumericBySex,
    models.FactMeasurementNumericByAgeSex,
    models.FactMeasurementCategorical,
    models.FactMeasurementCategoricalByAge,
    models.FactMeasurementCategoricalBySex,
    models.FactMeasurementCategoricalByAgeSex,
]
