#!/usr/bin/env python3
"""Static compatibility checker for chery+wuling against FrogPilot tip.

Catches: missing imports, missing symbols, missing abstract method impls,
renamed/removed upstream APIs, capnp field references that no longer exist.
"""
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/macbook/Code/openpilot/garudapilot")
CAR_DIRS = ["selfdrive/car/chery", "selfdrive/car/wuling"]
SAFETY_DIR = "panda/board/safety"

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RESET = "\033[0m"

def run(cmd, cwd=REPO):
    return subprocess.check_output(cmd, shell=True, cwd=cwd, text=True, stderr=subprocess.STDOUT)

def tree_files():
    return set(run("git ls-tree -r HEAD --name-only").splitlines())

def show_file(path):
    try:
        return run(f"git show HEAD:{path}")
    except subprocess.CalledProcessError:
        return None

def parse_py(path):
    src = show_file(path)
    if src is None:
        return None
    try:
        return ast.parse(src, filename=path)
    except SyntaxError as e:
        return e

def section(title):
    print(f"\n{YELLOW}{'=' * 60}{RESET}")
    print(f"{YELLOW}{title}{RESET}")
    print(f"{YELLOW}{'=' * 60}{RESET}")

# 1. MISSING FILES
def check_missing_files():
    section("1. FILES — are all expected files present in HEAD?")
    files = tree_files()
    expected = []
    for d in CAR_DIRS:
        for f in run(f"git show backup/FP-Staging-032026:{d} 2>/dev/null || true").split():
            pass
    # simpler: list expected files
    expected_paths = []
    for d in CAR_DIRS:
        for line in run(f"git show HEAD:{d}/__init__.py 2>/dev/null; echo marker").split("\n"):
            pass
    # just enumerate by ls-tree on HEAD
    for d in CAR_DIRS:
        for line in run(f"git ls-tree -r HEAD --name-only").splitlines():
            if line.startswith(d + "/"):
                expected_paths.append(line)
    expected = set(expected_paths)
    expected |= {
        "panda/board/safety/safety_chery.h",
        "panda/board/safety/safety_wuling.h",
        "opendbc/chery.dbc",
        "opendbc/chery_canfd.dbc",
        "opendbc/wuling_almazrs_generated.dbc",
        "selfdrive/debug/chery_test.py",
        "common/op_params.py",
        "common/colors.py",
        "livetuner.py",
    }
    missing = expected - files
    if missing:
        print(f"{RED}MISSING:{RESET}")
        for m in sorted(missing):
            print(f"  {m}")
    else:
        print(f"{GREEN}all expected files present{RESET}")

# 2. IMPORT RESOLUTION
def check_imports():
    section("2. IMPORTS — do all imported names resolve in HEAD?")
    files = tree_files()
    for d in CAR_DIRS:
        for path in sorted(files):
            if not path.startswith(d + "/") or not path.endswith(".py"):
                continue
            tree = parse_py(path)
            if not isinstance(tree, ast.AST):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module is None or node.level > 0:
                        continue
                    mod = node.module
                    # map openpilot.X.Y to self path
                    if mod.startswith("openpilot."):
                        candidate = mod[len("openpilot."):].replace(".", "/")
                        if not any(f.startswith(candidate + ".") or f == candidate or f.startswith(candidate + "/") for f in files):
                            print(f"{RED}BROKEN MODULE{RESET} {path}: from {mod}")
                            for n in node.names:
                                print(f"    -> {n.name}")
                            continue
                        # check symbol
                        for n in node.names:
                            target_file = None
                            for f in files:
                                if f == candidate + ".py" or (f.startswith(candidate + "/") and f.endswith(".py")):
                                    target_file = f
                                    break
                            if target_file:
                                src = show_file(target_file)
                                if src and re.search(rf"^def {n.name}\b|^class {n.name}\b|^{n.name}\s*=", src, re.M) is None:
                                    if n.name == "*":
                                        continue
                                    print(f"{RED}MISSING SYMBOL{RESET} {path}: from {mod} import {n.name}")

# 3. ABSTRACT METHOD COMPLIANCE
def check_abstract_methods():
    section("3. ABSTRACT METHODS — do chery/wuling implement all base abstract methods?")
    interfaces_src = show_file("selfdrive/car/interfaces.py")
    if not interfaces_src:
        print(f"{RED}interfaces.py missing!{RESET}")
        return
    # extract abstract methods from CarControllerBase, CarStateBase, RadarInterfaceBase, CarInterfaceBase
    def extract_abstract_methods(class_name):
        m = re.search(rf"class {class_name}.*?(?=\nclass |\Z)", interfaces_src, re.S)
        if not m:
            return []
        body = m.group(0)
        # crude: find @abstractmethod followed by def name
        return re.findall(r"@abstractmethod\s*\n\s*def (\w+)", body)
    abstracts = {}
    for cn in ["CarInterfaceBase", "CarControllerBase", "CarStateBase", "RadarInterfaceBase"]:
        abstracts[cn] = extract_abstract_methods(cn)
        print(f"  {cn} abstracts: {abstracts[cn]}")
    # now check chery/wuling implementations
    for d, bases in [("selfdrive/car/chery", ["CarInterfaceBase", "CarControllerBase", "CarStateBase", "RadarInterfaceBase"]),
                      ("selfdrive/car/wuling", ["CarInterfaceBase", "CarControllerBase", "CarStateBase", "RadarInterfaceBase"])]:
        for fname in ["interface.py", "carcontroller.py", "carstate.py", "radar_interface.py"]:
            fpath = f"{d}/{fname}"
            src = show_file(fpath)
            if not src:
                continue
            # find which base class is inherited
            base_match = re.search(r"class\s+\w+\s*\(([^)]+)\)", src)
            if not base_match:
                continue
            bases_inh = [b.strip() for b in base_match.group(1).split(",")]
            for b in bases_inh:
                if b in abstracts and abstracts[b]:
                    impls = set(re.findall(r"def (\w+)\s*\(", src))
                    for am in abstracts[b]:
                        if am not in impls:
                            print(f"{RED}MISSING IMPL{RESET} {fpath}: {b}.{am}")

# 4. CAPNP FIELD REFERENCES
def check_capnp_refs():
    section("4. CAPNP FIELDS — do chery/wuling capnp refs exist in new car.capnp?")
    capnp_src = show_file("cereal/car.capnp")
    if not capnp_src:
        print(f"{RED}car.capnp missing{RESET}")
        return
    # find struct names
    structs = re.findall(r"struct\s+(\w+)", capnp_src)
    print(f"  defined structs: {structs[:20]}...")
    # chery/wuling often set fields like ret.vEgo = ... ; patterns
    # we'll just extract `.attr` assignments from chery/wuling files and check most common
    attr_uses = {}
    for d in CAR_DIRS:
        for fname in ["carcontroller.py", "carstate.py", "interface.py"]:
            src = show_file(f"{d}/{fname}")
            if not src:
                continue
            for m in re.finditer(r"\.(\w+)\s*=", src):
                attr_uses[m.group(1)] = attr_uses.get(m.group(1), 0) + 1
    top_attrs = sorted(attr_uses.items(), key=lambda x: -x[1])[:25]
    print(f"  top attrs used: {[a for a, _ in top_attrs]}")
    # crude check: ensure top attrs appear in capnp (covers common ones)
    for a, c in top_attrs:
        if a in ("vEgo", "aEgo", "steeringAngleDeg", "steerFaultPermanent", "steerFaultTemporary",
                 "enabled", "active", "espDisabled", "standstill", "cruiseState", "steerRatio",
                 "vCruise", "buttonEvents", "canValid", "params", "longControlState", "speed",
                 "accel", "longitudinalPlan", "steer", "orientationNED", "yawRate", "events",
                 "steeringPressed", "steerFault", "actuators", "cruvState"):
            continue
        # skip if clearly local
        if re.search(rf"\b{a}\b", capnp_src) is None:
            print(f"{YELLOW}WARN{RESET} attr .{a} (used {c}x) not found in car.capnp (may be local var)")

# 5. SAFETY HOOK REGISTRATION
def check_safety_hooks():
    section("5. SAFETY HOOKS — are chery/wuling hooks registered correctly?")
    safety_src = show_file("panda/board/safety.h")
    if not safety_src:
        print(f"{RED}safety.h missing{RESET}")
        return
    # find the dispatch / hooks pattern
    for brand in ["chery", "wuling"]:
        sh = show_file(f"panda/board/safety/safety_{brand}.h")
        if not sh:
            print(f"{RED}safety_{brand}.h missing{RESET}")
            continue
        # extract function names defined
        funcs = re.findall(r"static\s+\w+\s+\*?\s*(\w+)\s*\(", sh)
        print(f"  safety_{brand}.h defines: {funcs}")
        # verify each is referenced in safety.h
        for fn in funcs:
            if fn in ("rx_hook", "tx_hook", "init", "fwd_hook", "get_valid_obd_signal"):
                # these are conventional names; check that brand-prefixed ones are wired
                pass
        # find brand-prefixed functions like chery_init, chery_rx_hook, chery_tx_hook
        brand_funcs = [f for f in funcs if brand in f]
        for bf in brand_funcs:
            if bf not in safety_src:
                print(f"{RED}NOT WIRED{RESET} safety_{brand}.h defines {bf} but safety.h doesn't reference it")

# 6. FROGPILOT CC_LONG / BUTTON SPAM
def check_frogpilot_integration():
    section("6. FROGPILOT INTEGRATION — CC_LONG / button spam hooks")
    fp_vars = show_file("frogpilot/common/frogpilot_variables.py")
    if not fp_vars:
        print(f"{RED}frogpilot_variables.py missing{RESET}")
        return
    # wuling expects FrogPilot CC_LONG hooks
    expected = ["has_cc_long", "cc_long", "experimental_mode", "experimentalMode"]
    for kw in expected:
        if kw not in fp_vars:
            print(f"{YELLOW}WARN{RESET} '{kw}' not found in frogpilot_variables.py")
        else:
            print(f"  {GREEN}found{RESET} '{kw}'")

# 7. CARD.PY REGISTRATION
def check_card_registration():
    section("7. CAR REGISTRY — are chery/wuling in card.py / values.py?")
    card_src = show_file("selfdrive/car/card.py")
    values_src = show_file("selfdrive/car/values.py")
    for name in ["CHERY", "chery", "WULING", "wuling"]:
        for label, src in [("card.py", card_src), ("values.py", values_src)]:
            if src and name in src:
                print(f"  {GREEN}found{RESET} '{name}' in {label}")
            elif src:
                print(f"  {YELLOW}MISSING{RESET} '{name}' in {label}")

if __name__ == "__main__":
    print(f"{YELLOW}chery+wuling compat check vs HEAD (= FP-Staging-112026){RESET}")
    check_missing_files()
    check_imports()
    check_abstract_methods()
    check_capnp_refs()
    check_safety_hooks()
    check_frogpilot_integration()
    check_card_registration()
    print(f"\n{GREEN}DONE{RESET}")