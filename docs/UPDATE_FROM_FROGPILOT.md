# Update garudapilot from FrogPilot upstream

Workflow when new `frogpilot/FrogPilot-Staging` release drops. Forward-ports chery + wuling car support onto new tip.

## Topology (after update)

```
FP-Staging-XXXXXX        ← new forward-port (target)
backup/FP-Staging-YYYYYY ← pristine copy of last release branch
FP-Staging-YYYYYY        ← squashed tidy history on old root
```

## Steps

### 1. Prep
```bash
cd garudapilot
git status                                    # clean
git fetch frogpilot FrogPilot-Staging
```

### 2. Backup last release branch
```bash
git branch backup/FP-Staging-YYYYYY FP-Staging-YYYYYY
```

### 3. Squash `FP-Staging-YYYYYY` into 3 logical commits on old root
```bash
git reset --hard backup/FP-Staging-YYYYYY
git reset --soft $(git rev-list --max-parents=0 backup/FP-Staging-YYYYYY)
git reset HEAD                                # unstage
```

Then 3 commits in this order: **feat → infra → docs**.

```bash
# commit 1: feat — new files only
git add selfdrive/car/chery/ \
  selfdrive/car/wuling/__init__.py selfdrive/car/wuling/carcontroller.py \
  selfdrive/car/wuling/carstate.py selfdrive/car/wuling/fingerprints.py \
  selfdrive/car/wuling/interface.py selfdrive/car/wuling/radar_interface.py \
  selfdrive/car/wuling/values.py selfdrive/car/wuling/wulingcan.py \
  panda/board/safety/safety_chery.h panda/board/safety/safety_wuling.h \
  opendbc/chery.dbc opendbc/chery_canfd.dbc opendbc/wuling_almazrs_generated.dbc \
  'frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022.json' \
  'frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022 copy.json' \
  'frogpilot/assets/nnff_models/WULING ALMAZ RS PRO 2022-ori.json' \
  selfdrive/debug/chery_test.py
git commit -m "feat(cars): add Chery & Wuling car support"

# commit 2: infra — modifications to existing files
git add -f .vscode/settings.json
git add cereal/car.capnp cereal/custom.capnp \
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
git commit -m "feat(cars): wire Chery & Wuling into FrogPilot harness"

# commit 3: docs — TUNING.md
git add selfdrive/car/wuling/TUNING.md
git commit -m "docs(cars): add Wuling tuning notes"

# move pointer + drop working-tree mods from periodic upstream patches
git checkout -- .
git status --short | wc -l                   # expect 0
```

### 4. Create new branch from upstream + revert Compile FrogPilot
```bash
git checkout -b FP-Staging-XXXXXX frogpilot/FrogPilot-Staging
git revert --no-edit HEAD                     # if tip is "Compile FrogPilot"
```

`frogpilot/FrogPilot-Staging` tip is normally a `Compile FrogPilot` squash. Revert it to match the v0.9.7 baseline that chery/wuling was written against.

### 5. Generate + apply patch
```bash
git diff ffdcf77f..backup/FP-Staging-YYYYYY > /tmp/chery-wuling.patch
git apply --check --3way /tmp/chery-wuling.patch
git apply --3way /tmp/chery-wuling.patch
```

`ffdcf77f` = "Revert Compile FrogPilot" from last cycle. Excludes periodic FrogPilot re-applies that the new tip already contains.

`--3way` auto-resolves most conflicts via git's three-way merge. Remaining conflicts land on infra files — fix manually, then `git add`.

### 6. Recreate 3 logical commits on new branch
Same 3-stage add/commit sequence as step 3. Working tree already has all changes from `git apply`.

```bash
git reset HEAD                                # unstage
# repeat the 3 `git add ... && git commit` from step 3
```

### 7. Static compat checks
```bash
# Python imports + abstract methods
python3 /tmp/compat_check.py

# DBC signal consistency
python3 /tmp/dbc_check.py

# manual spot checks
grep "chery\|wuling" selfdrive/car/values.py
grep -E "SAFETY_(CHERY|WULING)|chery_hooks|wuling_hooks" panda/board/safety.h
grep "SafetyModel" selfdrive/car/chery/interface.py selfdrive/car/wuling/interface.py
```

### 8. Compile verify (requires openpilot Docker toolchain)
```bash
scons -j$(nproc)
```

Catches: panda C hook signature drift, capnp schema codegen, missing panda constants (`FLAG_CHERY_LONG_CONTROL` etc.).

### 9. Push
```bash
git push -u origin FP-Staging-XXXXXX
```

## Compatibility risk hotspots

| Area | Why fragile | Mitigation |
|---|---|---|
| `panda/board/safety.h` | Macro/struct changes between FrogPilot releases | Always revert `Compile FrogPilot` first |
| `panda/board/safety/safety_{chery,wuling}.h` | Version-locked to specific `safety_hooks` shape | scons build will fail loudly if struct layout changed |
| `cereal/car.capnp` | Schema evolves, field indices shift | Forward-port must be additive only — never drop upstream fields |
| `selfdrive/car/interfaces.py` | `CarInterfaceBase` / `CarControllerBase` signatures change | Verify `_get_params`, `_update`, `update` match base |
| `selfdrive/car/__init__.py` | New helpers added, old ones may rename | chery/wuling must use latest `dbc_dict`, `Platforms`, `PlatformConfig` |
| `frogpilot/common/frogpilot_variables.py` | FrogPilot-specific keys (`has_cc_long`, `experimental_mode`) | Check keys still exist |
| `common/op_params.py` | Either kept as FrogPilot fork or replaced | chery/wuling still imports `opParams` — must exist |

## DBC alignment check

Safety board IDs must match DBC message IDs:

| Brand | DBC | Safety header |
|---|---|---|
| Chery | `opendbc/chery_canfd.dbc` | `panda/board/safety/safety_chery.h` |
| Wuling | `opendbc/wuling_almazrs_generated.dbc` | `panda/board/safety/safety_wuling.h` |

Quick eyeball:
```bash
for brand in chery wuling; do
  echo "=== $brand ==="
  grep "^#define ${brand^^}_[A-Z_0-9]\+\s\+0x" panda/board/safety/safety_${brand}.h | \
    awk '{print $3}' | while read hex; do
      printf "%s = %d dec\n" $hex $((hex))
    done
  echo "--- DBC IDs ---"
  grep "^BO_" opendbc/${brand}*.dbc | awk '{print $2, $3}'
done
```

Every `0x...` from safety header must equal a decimal ID in the matching DBC.

## Rollback

```bash
# restore last release branch from backup
git branch -f FP-Staging-YYYYYY backup/FP-Staging-YYYYYY

# delete failed forward-port
git branch -D FP-Staging-XXXXXX

# delete backup (only if you're sure)
git branch -D backup/FP-Staging-YYYYYY
```

## Original (full) history

If you ever need the un-squashed commit-by-commit history of a release:

```bash
git log --oneline backup/FP-Staging-YYYYYY
```

`backup/FP-Staging-*` branches are immutable — never run `git reset` on them.

## Scripts

`/tmp/compat_check.py` — import + abstract-method + safety-wiring check
`/tmp/dbc_check.py` — CAN signal/DBC consistency check

Both are static-analysis only. Real verification needs `scons` build.