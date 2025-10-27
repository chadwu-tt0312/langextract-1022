import langextract as lx

# Method 1: Using factory directly with provider parameter
config = lx.factory.ModelConfig(
    model_id="gpt-4",
    provider="OpenAILanguageModel",  # Explicit provider
    provider_kwargs={"api_key": "..."},
)
model = lx.factory.create_model(config)

# Method 2: Using provider without model_id (uses provider's default)
config = lx.factory.ModelConfig(
    provider="GeminiLanguageModel",  # Will use default gemini-2.5-flash
    provider_kwargs={"api_key": "..."},
)
model = lx.factory.create_model(config)

# Method 3: Auto-detection (when no conflicts exist)
config = lx.factory.ModelConfig(
    model_id="gemini-2.5-flash"  # Provider auto-detected
)
model = lx.factory.create_model(config)
