class SkillEngineError(Exception):
    """Base exception for all skill-engine errors."""

class SkillLoadError(SkillEngineError):
    """Raised when a skill module cannot be loaded (missing route, syntax error, etc)."""

class SkillNotFoundError(SkillEngineError):
    """Raised when a skill ID does not exist."""
