class ProjectGenerationLLMError(Exception):
    """Raised when project generation LLM call fails."""


class ProjectGenerationParseError(Exception):
    """Raised when generated project payload cannot be parsed or validated."""


class ProjectPersistenceError(Exception):
    """Raised when generated projects cannot be persisted."""
