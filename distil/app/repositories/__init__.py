"""Repository layer.

Public API:
* ``protocols`` — abstract interfaces (Protocols) that services depend on.
* ``postgres`` — async SQLAlchemy implementations.
* ``fake`` — in-memory implementations for fast tests and local fixtures.
"""

from app.repositories.protocols import (
    ActionRepositoryProtocol,
    AuditRepositoryProtocol,
    TextRepositoryProtocol,
)

__all__ = [
    "ActionRepositoryProtocol",
    "AuditRepositoryProtocol",
    "TextRepositoryProtocol",
]