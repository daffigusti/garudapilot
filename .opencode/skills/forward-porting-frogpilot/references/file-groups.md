# File groups for the 3 squash commits

When squashing `FP-Staging-YYYYYY` into 3 logical commits, stage these file lists in order.

## Commit 1 — feat(cars): add Chery & Wuling car support

**New files only.** What chery+wuling brings into existence.

```
selfdrive/car/chery/                                         (entire dir)
selfdrive/car/wuling/__init__.py
selfdrive/car/wuling/carcontroller.py
selfdrive/car/wuling/carstate.py
selfdrive/car/wuling/fingerprints.py
selfdrive/car/wuling/interface.py
selfdrive/car/wuling/radar_interface.py
selfdrive/car/wuling/values.py
selfdrive/car/wuling/wulingcan.py
panda/board/safety/safety_chery.h
panda/board/safety/safety_wuling.h
opendbc/chery.dbc
opendbc/chery_canfd.dbc
opendbc/wuling_almazrs_generated.dbc
frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022.json
frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022 copy.json
frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022-ori.json
selfdrive/debug/chery_test.py
```

Note: `selfdrive/car/wuling/TUNING.md` is in commit 3 (docs), not here.

```bash
git add \
  selfdrive/car/chery/ \
  selfdrive/car/wuling/__init__.py \
  selfdrive/car/wuling/carcontroller.py \
  selfdrive/car/wuling/carstate.py \
  selfdrive/car/wuling/fingerprints.py \
  selfdrive/car/wuling/interface.py \
  selfdrive/car/wuling/radar_interface.py \
  selfdrive/car/wuling/values.py \
  selfdrive/car/wuling/wulingcan.py \
  panda/board/safety/safety_chery.h \
  panda/board/safety/safety_wuling.h \
  opendbc/chery.dbc \
  opendbc/chery_canfd.dbc \
  opendbc/wuling_almazrs_generated.dbc \
  'frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022.json' \
  'frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022 copy.json' \
  'frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022-ori.json' \
  selfdrive/debug/chery_test.py
```

## Commit 2 — feat(cars): wire Chery & Wuling into FrogPilot harness

**Modifications to existing files.** How chery+wuling integrate into FrogPilot.

```
cereal/car.capnp
cereal/custom.capnp
common/colors.py
common/op_params.py
common/params.cc
common/travis_checker.py
frogpilot/common/frogpilot_variables.py
frogpilot/ui/qt/offroad/vehicle_settings.cc
launch_env.sh
livetuner.py
opendbc/can/common.h
opendbc/can/parser.cc
panda/board/safety.h
panda/python/__init__.py
panda/tests/echo.py
panda/tests/panda_test.py
selfdrive/car/card.py
selfdrive/car/fingerprints.py
selfdrive/car/interfaces.py
selfdrive/car/torque_data/override.toml
selfdrive/car/torque_data/params.toml
selfdrive/car/values.py
selfdrive/controls/controlsd.py
selfdrive/controls/lib/drive_helpers.py
selfdrive/controls/lib/events.py
selfdrive/controls/lib/latcontrol_pid.py
selfdrive/locationd/torqued.py
system/version.py
.gitignore
.github/update_date
.vscode/settings.json   # gitignored — add with -f
```

```bash
git add -f .vscode/settings.json
git add \
  cereal/car.capnp cereal/custom.capnp \
  common/colors.py common/op_params.py common/params.cc common/travis_checker.py \
  frogpilot/common/frogpilot_variables.py \
  frogpilot/ui/qt/offroad/vehicle_settings.cc \
  launch_env.sh livetuner.py \
  opendbc/can/common.h opendbc/can/parser.cc \
  panda/board/safety.h panda/python/__init__.py \
  panda/tests/echo.py panda/tests/panda_test.py \
  selfdrive/car/card.py selfdrive/car/fingerprints.py selfdrive/car/interfaces.py \
  selfdrive/car/torque_data/override.toml selfdrive/car/torque_data/params.toml \
  selfdrive/car/values.py \
  selfdrive/controls/controlsd.py \
  selfdrive/controls/lib/drive_helpers.py selfdrive/controls/lib/events.py \
  selfdrive/controls/lib/latcontrol_pid.py \
  selfdrive/locationd/torqued.py \
  system/version.py \
  .gitignore .github/update_date
```

## Commit 3 — docs(cars): add Wuling tuning notes

```
selfdrive/car/wuling/TUNING.md
```

```bash
git add selfdrive/car/wuling/TUNING.md
```

## Total: 55 files / +5705 / -172 lines

## Working-tree cleanup after squash

Periodic FrogPilot re-applies (commits 4-10 of last release) leave untracked/modified working-tree files that shouldn't be on the cleaned branch:

```bash
git checkout -- .
# leftover untracked from periodic patches — review before deleting
git status --short
# most are workflows/holiday themes — safe to remove if not needed
```

## Patch source for forward-port

Always use `ffdcf77f..backup/$LAST` as the diff base, NOT `c68d6b34..backup/$LAST`:

- `c68d6b34` = "openpilot v0.9.7 release" — the very first commit, includes baseline FrogPilot files
- `ffdcf77f` = "Revert Compile FrogPilot" — first commit of chery+wuling work, excludes periodic FrogPilot re-applies

```bash
git diff ffdcf77f..backup/$LAST > /tmp/chery-wuling.patch
```

If `ffdcf77f` is missing from your backup (different release cycle), use the **first chery+wuling commit** (`Add Chery & Wuling` = `ded81f5d` in last cycle) as the boundary instead.