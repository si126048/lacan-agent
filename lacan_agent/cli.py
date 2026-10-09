"""Command line interface for Lacan-Agent.

The CLI is deliberately dependency-light so the complete Mock workflow works
without a web server or an API key.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .db import Store
from .models import ConsentScope, Participant, Project, ReviewDecision, ReviewRequest
from .rag import ingest, search
from .workflow import Workflow

EXIT_USAGE = 2
EXIT_DOMAIN = 3


class CliError(RuntimeError):
    """A user-facing error with a stable exit code."""

    def __init__(self, message: str, code: int = EXIT_DOMAIN):
        super().__init__(message)
        self.code = code


def _json(value: Any, pretty: bool = False) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2 if pretty else None, default=str)


def _emit(value: Any, *, pretty: bool, output: str | None = None) -> None:
    text = _json(value, pretty)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text + "\n", encoding="utf-8")
        print(_json({"written": str(Path(output).resolve())}, pretty=False))
    else:
        print(text)


def _ensure_project(store: Store, project_id: str) -> Project:
    project = store.get_project(project_id)
    if project is None:
        project = store.create_project(Project(id=project_id))
    return project


def _source_for(store: Store, project_id: str, participant_id: str, source: str):
    docs = store.list_documents(project_id, participant_id)
    matches = [d for d in docs if d.id == source or d.origin == source or Path(d.origin).name == source]
    if not matches:
        raise CliError(f"source not found: {source}")
    if len(matches) > 1:
        raise CliError(f"source is ambiguous: {source}; use its document id")
    return matches[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lacan-agent",
        description="Evidence-constrained Lacan-Agent research workflow (local Mock mode).",
    )
    parser.add_argument("--db", default=os.getenv("LACAN_DB_PATH", "./data/lacan.db"), help="SQLite path")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    parser.add_argument("--output", help="write the command result to a JSON file")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("interactive", aliases=["shell"], help="open the guided interactive terminal UI")

    p = sub.add_parser("init", help="create a local project")
    p.add_argument("--project", default="demo")

    p = sub.add_parser("ingest-theory", help="ingest a TXT, Markdown, or digital PDF theory source")
    p.add_argument("--path", required=True); p.add_argument("--project", default="demo")

    p = sub.add_parser("theory-search", aliases=["search"], help="search ingested theory sources")
    p.add_argument("query"); p.add_argument("--project", default="demo"); p.add_argument("--limit", type=int, default=5)

    p = sub.add_parser("add-participant", help="register an anonymised participant")
    p.add_argument("--id", required=True); p.add_argument("--project", default="demo"); p.add_argument("--consent", required=True)

    p = sub.add_parser("add-source", help="ingest an authorised participant source")
    p.add_argument("--participant", required=True); p.add_argument("--project", default="demo"); p.add_argument("--file", required=True)

    p = sub.add_parser("analyze", help="run the Evidence -> Interpreter -> Critic Mock workflow")
    p.add_argument("--participant", required=True); p.add_argument("--project", default="demo"); p.add_argument("--source", required=True)
    p.add_argument("--idempotency-key", default="cli-run"); p.add_argument("--mock", action="store_true", help="use the built-in provider")

    p = sub.add_parser("run-show", aliases=["status"], help="show a run, including audit events")
    p.add_argument("--run", required=True)

    p = sub.add_parser("review", help="approve, reject, or request revision")
    p.add_argument("--run", required=True); p.add_argument("--decision", choices=[x.value for x in ReviewDecision], required=True)
    p.add_argument("--reviewer", default="reviewer-1"); p.add_argument("--reason", default="")

    p = sub.add_parser("export", help="export an approved packet and typed graph")
    p.add_argument("--run", required=True); p.add_argument("--format", choices=["json"], default="json")

    p = sub.add_parser("withdraw", help="withdraw a participant and block future analysis")
    p.add_argument("--participant", required=True); p.add_argument("--project", default="demo")
    return parser


def execute(args: argparse.Namespace) -> Any:
    if args.command in {"interactive", "shell"}:
        from .interactive import run_interactive
        return run_interactive(args.db)
    store = Store(args.db)
    provider = None
    if getattr(args, 'mock', False):
        from .llm import FakeProvider
        provider = FakeProvider()
    elif os.environ.get("DASHSCOPE_API_KEY"):
        from .llm import QwenProvider
        provider = QwenProvider()
    flow = Workflow(store, provider)
    cmd = args.command
    if cmd == "init":
        return _ensure_project(store, args.project).model_dump()
    if cmd == "ingest-theory":
        _ensure_project(store, args.project)
        return ingest(store, args.path, args.project).model_dump(exclude={"text"})
    if cmd in {"theory-search", "search"}:
        _ensure_project(store, args.project)
        return {"items": search(store, args.query, max(1, min(args.limit, 5)))}
    if cmd == "add-participant":
        _ensure_project(store, args.project)
        try:
            consent = ConsentScope.model_validate(json.loads(Path(args.consent).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise CliError(f"invalid consent file: {exc}") from exc
        return store.put_participant(Participant(id=args.id, project_id=args.project, pseudonym=args.id, consent_scope=consent)).model_dump()
    if cmd == "add-source":
        participant = store.get_participant(args.project, args.participant)
        if participant is None:
            raise CliError(f"participant not found: {args.participant}")
        if participant.withdrawn_at or not participant.consent_scope.research_analysis:
            raise CliError("CONSENT_REQUIRED")
        return ingest(store, args.file, args.project, args.participant, participant.consent_scope).model_dump(exclude={"text"})
    if cmd == "analyze":
        participant = store.get_participant(args.project, args.participant)
        if participant is None:
            raise CliError(f"participant not found: {args.participant}")
        document = _source_for(store, args.project, args.participant, args.source)
        run = flow.run(args.project, args.participant, [document.id], args.idempotency_key)
        return {"run_id": run.id, "state": run.state}
    if cmd in {"run-show", "status"}:
        run = store.get_run(args.run)
        if run is None:
            raise CliError(f"run not found: {args.run}")
        return run.model_dump(mode="json")
    if cmd == "review":
        return flow.review(args.run, ReviewRequest(reviewer_id=args.reviewer, decision=args.decision, reason=args.reason)).model_dump(mode="json")
    if cmd == "export":
        return flow.export(args.run)
    if cmd == "withdraw":
        participant = store.withdraw(args.project, args.participant)
        if participant is None:
            raise CliError(f"participant not found: {args.participant}")
        return {"participant_id": args.participant, "state": "WITHDRAWAL_REQUESTED"}
    raise CliError(f"unknown command: {cmd}", EXIT_USAGE)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=os.environ.get('LACAN_LOG_LEVEL', 'WARNING'), format='%(levelname)s %(name)s: %(message)s')
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = execute(args)
        if isinstance(result, int):
            return result
        _emit(result, pretty=args.pretty, output=args.output)
        return 0
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code
    except (PermissionError, KeyError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_DOMAIN


if __name__ == "__main__":
    raise SystemExit(main())




