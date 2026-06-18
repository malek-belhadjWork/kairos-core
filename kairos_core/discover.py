"""Brick discovery + a one-call config runner.

After ``pip install kairos-core`` plus whatever brick packages you need, you don't
import bricks by hand:

    from kairos_core import run_config
    run_config("config.yaml")

Bricks are found via the ``kairos.bricks`` entry-point group: every brick package
registers itself there in its pyproject, so installing it makes it discoverable
by NAME — core knows nothing about specific bricks.
"""
from __future__ import annotations

from typing import Any

from .config import load_bundle, validate_section
from .pipeline import run_pipeline, wire


def discover_bricks() -> dict[str, Any]:
    """Return {brick NAME -> brick module} from installed ``kairos.bricks`` packages."""
    from importlib.metadata import entry_points

    found: dict[str, Any] = {}
    for ep in entry_points(group="kairos.bricks"):
        module = ep.load()
        found[getattr(module, "NAME", ep.name)] = module
    return found


def build(config_path):
    """Load a config bundle, validate each section against its discovered brick,
    wire sub-brick injections. Returns (bound_by_name, ordered_stage_list)."""
    bundle = load_bundle(config_path)
    bricks = discover_bricks()
    stage_names = bundle["pipeline"]
    brick_names = [k for k in bundle if k != "pipeline"]

    missing = [n for n in brick_names if n not in bricks]
    if missing:
        raise KeyError(
            f"config references unknown brick(s) {missing}; "
            f"installed: {sorted(bricks)}"
        )

    modules = {n: bricks[n] for n in brick_names}
    configs = {n: validate_section(modules[n], bundle[n]) for n in brick_names}
    bound = wire(modules, configs)
    return bound, [bound[s] for s in stage_names]


def run_config(config_path, data=None):
    """Build and run the pipeline described by a single config.yaml.

    Paths inside the config (e.g. ``./data/in``) resolve relative to the current
    working directory, so run from your project's directory."""
    _bound, stages = build(config_path)
    return run_pipeline(stages, data)
