class ProjectGenerationLLMError(Exception):
    """Raised when project generation LLM call fails."""


class ProjectGenerationParseError(Exception):
    """Raised when generated project payload cannot be parsed or validated."""


class ProjectPersistenceError(Exception):
    """Raised when generated projects cannot be persisted."""


class ProjectSelectionNotFoundError(Exception):
    """Raised when selected project id does not exist for user."""

class ProjectExpansionPersistenceError(Exception):
    """Raised when expanded project cannot be persisted."""
