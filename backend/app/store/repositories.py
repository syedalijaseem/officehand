"""Workspace-scoped data access.

Business code never queries tables directly. It goes through `ScopedRepository`, which takes a
`Scope` (not a bare ID) and adds `workspace_id = :ws` to every query. Objects from another
workspace are simply not found, so routes return 404 and don't reveal that they exist.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, SQLModel, select

from app.store.models import WorkspaceScoped

DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 500


class ScopeViolationError(Exception):
    """Raised when code tries to write an object into a workspace it doesn't belong to."""


@dataclass(frozen=True, slots=True)
class Scope:
    workspace_id: uuid.UUID


class ScopedRepository[T: WorkspaceScoped]:
    def __init__(self, session: Session, model: type[T]) -> None:
        if not (issubclass(model, SQLModel) and "workspace_id" in model.model_fields):
            raise TypeError(f"{model.__name__} has no workspace_id; it can't be scoped")
        self._session = session
        self._model = model

    def add(self, scope: Scope, obj: T) -> T:
        if obj.workspace_id is None:
            obj.workspace_id = scope.workspace_id
        elif obj.workspace_id != scope.workspace_id:
            raise ScopeViolationError(f"{self._model.__name__} belongs to another workspace")
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def get(self, scope: Scope, object_id: uuid.UUID) -> T | None:
        model: Any = self._model
        statement = select(model).where(model.id == object_id, model.workspace_id == scope.workspace_id)
        result: T | None = self._session.exec(statement).first()
        return result

    def list(self, scope: Scope, *, limit: int = DEFAULT_LIST_LIMIT, offset: int = 0) -> Sequence[T]:
        model: Any = self._model
        statement = (
            select(model)
            .where(model.workspace_id == scope.workspace_id)
            .order_by(model.id)
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), MAX_LIST_LIMIT))
        )
        results: Sequence[T] = self._session.exec(statement).all()
        return results
