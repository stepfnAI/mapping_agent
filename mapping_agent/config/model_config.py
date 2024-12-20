from sfn_blueprint import MODEL_CONFIG

MODEL_CONFIG["category_identifier"] = {
    "model": "gpt-4o-mini", #"gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 100,
    "n": 1,
    "stop": None
}

MODEL_CONFIG["column_mapper"] = {
    "model": "gpt-4o-mini", #"gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 500,
    "n": 1,
    "stop": None
}