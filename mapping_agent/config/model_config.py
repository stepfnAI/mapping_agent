from sfn_blueprint import MODEL_CONFIG

DEFAULT_LLM_PROVIDER = 'openai'
DEFAULT_LLM_MODEL = 'gpt-4o-mini'

MODEL_CONFIG["category_identifier"] = {
    "openai": {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 100,
        "n": 1,
        "stop": None
    }
}

MODEL_CONFIG["column_mapper"] = {
    "openai": {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 500,
        "n": 1,
        "stop": None
    }
}