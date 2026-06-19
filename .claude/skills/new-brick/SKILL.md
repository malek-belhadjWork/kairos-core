---
name: new-brick
description: Create a new Kairos brick as its own repo/package (kairos-<name>) — scaffold it, depend on kairos-core, register it for discovery, test it against the installed core, and publish. Use when adding a brick to the Kairos ecosystem.
---

# new-brick — add a Kairos brick (its own repo/package)

A **brick** = a generic **engine** (code, never edited per project) + a **config**
(the only project-specific surface). Every brick exposes `run(input, config) -> output`.
In Kairos each brick is **its own repo/package** named `kairos-<name>` that depends on
`kairos-core` and registers itself for discovery. This skill is the uniform recipe.

## 0. Decide the kind
- **engine + config** — one engine, behavior driven entirely by config.
- **registry** — a stable interface + interchangeable plugins; config picks one via
  `impl` and passes its `params` (use when implementations vary).

Pick a short lowercase `NAME` (e.g. `classify`). Package = `kairos-classify`,
import = `kairos_classify`, brick `NAME = "classify"` (config references it by NAME).

## 1. Create the repo
Create a **Private, empty** GitHub repo `kairos-<name>` (no README/.gitignore/license).

## 2. Layout
```
kairos-<name>/
  pyproject.toml
  kairos_<name>/
    __init__.py            # NAME/VERSION/KIND/CONFIG_MODEL/run  (+ REGISTRY if registry)
    config_model.py        # the brick's parameters
    engine.py              # engine kind  — OR — registry.py + interface.py + plugins/ (registry kind)
  tests/
    _harness.py            # copy from kairos-core/tests
    run_all.py             # copy from kairos-core/tests
    test_<name>.py
  .gitignore  README.md
```
Bricks import only the framework (`from kairos_core...`) — never another brick.

## 3. Scaffold the package

### Engine brick
`kairos_<name>/__init__.py`
```python
"""<NAME> — engine+config brick. <one-line>. KIND=engine."""
from __future__ import annotations
from .config_model import Config
from .engine import run

NAME = "<NAME>"; VERSION = "1.0.0"; KIND = "engine"; CONFIG_MODEL = Config
__all__ = ["NAME", "VERSION", "KIND", "CONFIG_MODEL", "run"]
```
`kairos_<name>/config_model.py`  ← the brick's parameters
```python
from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from kairos_core.config import BrickConfig

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Config(BrickConfig):
    # example_param: int = 0   (defaults = what a project gets when it omits the key)
    ...
```
`kairos_<name>/engine.py`
```python
from __future__ import annotations

def run(data, config):
    """data = previous stage's output; config = validated Config. Return the output."""
    ...
    return data
```

### Registry brick
`registry.py`
```python
from __future__ import annotations
from kairos_core.registry import Registry
REGISTRY = Registry(interface="(data, params) -> output")
```
`config_model.py`
```python
from __future__ import annotations
from kairos_core.config import RegistryConfig
class Config(RegistryConfig):
    """pick a plugin (`impl`) + pass its `params`."""
```
`__init__.py`
```python
from __future__ import annotations
from .config_model import Config
from .registry import REGISTRY
NAME = "<NAME>"; VERSION = "1.0.0"; KIND = "registry"; CONFIG_MODEL = Config
from . import plugins  # noqa: E402,F401  (registers plugins on import)

def run(data, config):
    return REGISTRY.create(config.impl, config.params)(data)
```
`plugins/__init__.py` → `from . import example` ; `plugins/example.py`
```python
from __future__ import annotations
from ..registry import REGISTRY

@REGISTRY.register("example")
def make_example(**params):
    def run(data):           # defer heavy third-party imports into here
        ...
        return data
    return run
```

## 4. `pyproject.toml` — depend on core + self-register
```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "kairos-<name>"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = ["kairos-core>=1.0"]      # + any libs this brick needs
                                         # + another brick (e.g. "kairos-ocr>=1.0") if you inject it

[tool.setuptools.packages.find]
include = ["kairos_<name>*"]

[project.entry-points."kairos.bricks"]
<name> = "kairos_<name>"                  # this is what makes it discoverable by NAME
```

## 5. Develop against the installed core
```bash
python -m venv .venv && .venv\Scripts\activate
pip install kairos-core            # from your registry, or: pip install -e ../kairos-core
pip install -e .                   # the brick, editable
python -c "import kairos_core; print(kairos_core.discover_bricks())"   # your brick shows up
```

## 6. Test (zero-dependency harness)
`tests/test_<name>.py`
```python
from _harness import harness
import kairos_<name> as brick
test = harness(__name__)

@test
def test_runs():
    cfg = brick.CONFIG_MODEL.model_validate({ ... })   # engine: settings dict
    # registry: {"impl": "example", "params": {...}}
    assert brick.run(<input>, cfg) == <expected>

if __name__ == "__main__":
    test.main()
```
```bash
python tests/run_all.py
```

## 7. README (required)
Every brick ships a `README.md` so a consumer can write its config without reading
the code. Fill in this template:

```markdown
# kairos-<name>

**Kind:** engine|registry · **NAME:** `<name>` · depends on `kairos-core`

<one line: what the brick does>

- **Input:** <shape it receives>
- **Output:** <shape it returns>

## Install
\`\`\`bash
pip install kairos-core kairos-<name>
\`\`\`
<note any external requirement, e.g. a system binary>

## Config
\`\`\`yaml
# engine brick — the section IS the settings, flat:
<name>:
  some_param: <value>
# registry brick — pick a plugin + its params:
# <name>: {impl: <plugin>, params: {...}}
\`\`\`

| key | default | meaning |
|-----|---------|---------|
| `some_param` | `...` | ... |

<!-- registry bricks: also a table of each `impl` and its params -->
```

## 8. Publish
```bash
git init -b main && git add -A && git commit -m "kairos-<name> v1.0.0"
git remote add origin https://github.com/<you>/kairos-<name>.git
git push -u origin main
git tag v1.0.0 && git push --tags          # pin-able release
# later: build + twine upload to the private PyPI registry
```

## 9. Use it in a project
```bash
pip install kairos-core kairos-<name>      # (or add to a project's requirements)
```
```yaml
# config.yaml
pipeline: [<name>, ...]                     # add as a stage (omit if it's a sub-brick)
<name>: { ...settings... }                  # engine — or — {impl: example, params: {...}} for registry
```

## Sub-brick dependency (like extract → ocr)
If your brick calls another brick that is NOT a stage:
- `INJECTS = {"<attr>": "<dep_brick_name>"}` in `__init__.py`,
- `<attr>: Any = Field(default=None, exclude=True)` on its `Config`,
- call `config.<attr>(...)` in the engine,
- add the dependency package to `pyproject.toml` (`dependencies = [..., "kairos-<dep>>=1.0"]`).
`kairos_core.wire` builds the dependency from its own config section and injects it.

## Checklist
- [ ] repo `kairos-<name>` created (Private, empty)
- [ ] `kairos_<name>/` with the right files for its KIND; params in `config_model.py`
- [ ] `pyproject.toml`: depends on `kairos-core`, entry point `[project.entry-points."kairos.bricks"]`
- [ ] `tests/test_<name>.py` green via `python tests/run_all.py`
- [ ] `README.md` documents purpose + every config parameter (and `impl`s if registry)
- [ ] committed, pushed, tagged; (published to the registry when ready)
