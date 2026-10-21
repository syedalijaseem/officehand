import time
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.store.db import create_db_engine, init_db
from app.store.ids import uuid7
from app.store.models import Document, Workspace
from app.store.repositories import Scope, ScopedRepository, ScopeViolationError


@pytest.fixture
def session(tmp_path: Path) -> Session:
    engine = create_db_engine(tmp_path / "test.db")
    init_db(engine)
    return Session(engine)


def test_uuid7_has_version_7_and_is_time_ordered() -> None:
    first = uuid7()
    time.sleep(0.002)
    second = uuid7()

    assert isinstance(first, uuid.UUID)
    assert first.version == 7
    assert first.variant == uuid.RFC_4122
    assert first < second


def test_sqlite_pragmas_enable_wal_foreign_keys_and_busy_timeout(session: Session) -> None:
    assert session.exec(text("PRAGMA journal_mode")).one()[0] == "wal"  # type: ignore[call-overload]
    assert session.exec(text("PRAGMA foreign_keys")).one()[0] == 1  # type: ignore[call-overload]
    assert session.exec(text("PRAGMA busy_timeout")).one()[0] == 5000  # type: ignore[call-overload]


def _two_workspaces(session: Session) -> tuple[Scope, Scope]:
    ws_a, ws_b = Workspace(name="Juniper Ridge"), Workspace(name="Other Co")
    session.add_all([ws_a, ws_b])
    session.commit()
    return Scope(workspace_id=ws_a.id), Scope(workspace_id=ws_b.id)


def _document(title: str) -> Document:
    return Document(
        drive_file_id=f"drive-{title}",
        title_enc=f"enc:{title}",
        mime_type="application/pdf",
        project_id="P-101",
    )


def test_repository_sets_workspace_on_add(session: Session) -> None:
    scope_a, _ = _two_workspaces(session)
    repo = ScopedRepository(session, Document)

    saved = repo.add(scope_a, _document("contract"))

    assert saved.workspace_id == scope_a.workspace_id


def test_repository_refuses_object_from_another_workspace(session: Session) -> None:
    scope_a, scope_b = _two_workspaces(session)
    repo = ScopedRepository(session, Document)
    foreign = _document("contract")
    foreign.workspace_id = scope_b.workspace_id

    with pytest.raises(ScopeViolationError):
        repo.add(scope_a, foreign)


def test_cross_workspace_get_and_list_return_nothing(session: Session) -> None:
    scope_a, scope_b = _two_workspaces(session)
    repo = ScopedRepository(session, Document)
    doc = repo.add(scope_a, _document("contract"))

    assert repo.get(scope_a, doc.id) is not None
    assert repo.get(scope_b, doc.id) is None
    assert [d.id for d in repo.list(scope_a)] == [doc.id]
    assert repo.list(scope_b) == []


def test_scoped_repository_rejects_unscoped_models(session: Session) -> None:
    with pytest.raises(TypeError, match="workspace_id"):
        ScopedRepository(session, Workspace)
