# KairosCore

The framework for modular pipeline **bricks**. A brick = a generic **engine**
(code, never edited per project) + a **config** (the only project-specific
surface). Every brick exposes `run(input, config) -> output`, so bricks compose
into pipelines. KairosCore is domain-agnostic; the bricks live in their own
packages (`kairos-ocr`, `kairos-extract`, …) and register themselves for
discovery.

## Install
```bash
pip install kairos-core
```

## What it provides
- the brick contract (`BrickConfig`, `RegistryConfig`, `Registry`),
- config loading + validation (`load_bundle`, `validate_section`),
- pipeline wiring + run (`wire`, `run_pipeline`),
- brick discovery (`discover_bricks`) and a one-call runner (`run_config`),
- `python -m kairos_core config.yaml`.

## Two kinds of brick
- **engine + config** — one engine, behavior driven entirely by config.
- **registry** — a stable interface + interchangeable plugins; config picks one
  via `impl` and passes its `params`.

## Discovery
Brick packages register under the `kairos.bricks` entry-point group, so installing
a brick makes it available by its `NAME` — core never imports a specific brick.

```python
from kairos_core import discover_bricks, run_config
discover_bricks()            # {name -> brick module} for installed bricks
run_config("config.yaml")    # load -> discover -> validate -> wire -> run
```

See `docs`/the `new-brick` workflow to author a brick.
