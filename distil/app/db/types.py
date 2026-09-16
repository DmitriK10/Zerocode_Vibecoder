"""Portable SQL types used across the project.

* ``JSONType`` maps to native ``JSONB`` on PostgreSQL and generic ``JSON``
  elsewhere (SQLite in tests).
* ``BigIntType`` keeps ``BIGINT`` on PostgreSQL but degrades to ``INTEGER``
  on SQLite, because SQLite only auto-increments ``INTEGER PRIMARY KEY``
  (the ``rowid`` alias). Using ``BIGINT PRIMARY KEY`` on SQLite causes
  ``NOT NULL constraint failed: <table>.id``.
"""

from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeEngine

JSONType: TypeEngine[object] = JSON().with_variant(JSONB(), "postgresql")

# BigInteger on PostgreSQL; INTEGER on SQLite so that PKs map to rowid.
BigIntType: TypeEngine[int] = BigInteger().with_variant(Integer, "sqlite")