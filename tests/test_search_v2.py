from pathlib import Path

from app.models import MemoryCreate, MemoryRole
from app.services.memory_store import MemoryStore
from app.utils.search_query import parse_search_query


def test_parse_search_query_extracts_structured_filters():
    plan = parse_search_query(
        'text:"aggregate split" role:decision topic:"Grid Planning" '
        'entity:"Transformer A" project:HVDC tag:topic/aggregate '
        "after:2026-03-01 before:2026-03-31 limit:7"
    )

    assert plan.text_terms == ["aggregate split"]
    assert [role.value for role in plan.roles] == ["decision"]
    assert plan.topics == ["Grid Planning"]
    assert plan.entities == ["Transformer A"]
    assert plan.projects == ["HVDC"]
    assert plan.tags == ["topic/aggregate"]
    assert plan.after.isoformat() == "2026-03-01"
    assert plan.before.isoformat() == "2026-03-31"
    assert plan.limit == 7


def test_save_derives_namespaced_tags(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    result = store.save(
        MemoryCreate(
            roles=[MemoryRole.decision],
            title="Derived tag note",
            content="Use derived tags for metadata lookup.",
            source="manual",
            topics=["Grid Planning"],
            entities=["Transformer A"],
            projects=["HVDC"],
            append_daily=False,
        )
    )

    item = store.get(result["id"])

    assert item is not None
    assert "role/decision" in item["tags"]
    assert "topic/grid-planning" in item["tags"]
    assert "entity/transformer-a" in item["tags"]
    assert "project/hvdc" in item["tags"]


def test_search_memory_query_dsl_filters_with_single_query_string(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    matched = store.save(
        MemoryCreate(
            roles=[MemoryRole.decision],
            title="Aggregate split decision",
            content="Shared planning content for voyage split.",
            source="manual",
            topics=["Grid Planning"],
            entities=["Transformer A"],
            projects=["HVDC"],
            append_daily=False,
        )
    )
    store.save(
        MemoryCreate(
            roles=[MemoryRole.decision],
            title="Other decision",
            content="Shared planning content for other project.",
            source="manual",
            topics=["Other Topic"],
            entities=["Other Entity"],
            projects=["Other Project"],
            append_daily=False,
        )
    )

    result = store.search(
        query='text:"shared planning content" role:decision topic:"Grid Planning" '
        'entity:"Transformer A" project:HVDC limit:5'
    )

    assert [row["id"] for row in result["results"]] == [matched["id"]]


def test_search_memory_matches_hyphenated_tokens(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    matched = store.save(
        MemoryCreate(
            roles=[MemoryRole.decision],
            title="ChatGPT Specialist Write Check 20260328-194027",
            content="Smoke-test title with a hyphenated timestamp token.",
            source="manual",
            append_daily=False,
        )
    )

    result = store.search(query="ChatGPT Specialist Write Check 20260328-194027")

    assert [row["id"] for row in result["results"]] == [matched["id"]]
