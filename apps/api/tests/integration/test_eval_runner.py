"""Eval runner smoke test."""

import pytest

from app.db.session import SessionLocal
from app.evals.run import run_eval_suite


@pytest.mark.asyncio
@pytest.mark.eval
async def test_eval_runner_smoke() -> None:
    async with SessionLocal() as db:
        report = await run_eval_suite(db, suite="golden")
    assert report["total"] >= 3
    assert report["passed"] >= 1
    assert all("case_id" in r and "pass" in r for r in report["results"])
