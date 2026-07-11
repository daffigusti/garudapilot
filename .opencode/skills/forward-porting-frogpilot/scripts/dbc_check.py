#!/usr/bin/env python3
"""Verify every CAN signal/message referenced in chery/wuling carstate.py
exists in the corresponding DBC file. Catches typos, missing definitions."""
import re
import subprocess
from pathlib import Path

REPO = Path("/Users/macbook/Code/openpilot/garudapilot")

def run(cmd):
    return subprocess.check_output(cmd, shell=True, cwd=REPO, text=True)

def show(path):
    return run(f"git show HEAD:{path}")

def parse_dbc(dbc_text):
    """Return {msg_name: {signal_name: {min,max,...}}}"""
    msgs = {}
    cur_msg = None
    for line in dbc_text.splitlines():
        m = re.match(r"^BO_\s+(\d+)\s+(\w+)\s*:", line)
        if m:
            msg_id, msg_name = int(m.group(1)), m.group(2)
            cur_msg = msg_name
            msgs[msg_name] = {"id": msg_id, "signals": {}}
            continue
        m = re.match(r"^\s+SG_\s+(\w+)\s*:", line)
        if m and cur_msg:
            sig = m.group(1)
            cur_min = float(re.search(r"[\d.]+\|[\d.]+", line).group().split("|")[0])
            cur_max = float(re.search(r"[\d.]+\|[\d.]+", line).group().split("|")[1])
            msgs[cur_msg]["signals"][sig] = {"min": cur_min, "max": cur_max}
        if line.strip() == "":
            cur_msg = None
    return msgs

def extract_signals_from_py(py_text):
    """Find all pt_cp.vl["MSG"]["SIG"] or pt_cp.vl["MSG"] patterns."""
    refs = []
    # pattern 1: cp.vl["MSG"]["SIG"]
    for m in re.finditer(r'\.vl\[\s*["\'](\w+)["\']\s*\]\[\s*["\'](\w+)["\']\s*\]', py_text):
        refs.append((m.group(1), m.group(2)))
    # pattern 2: cp.vl["MSG"]  (whole message access — no signal name)
    for m in re.finditer(r'\.vl\[\s*["\'](\w+)["\']\s*\]', py_text):
        if not any(r[0] == m.group(1) for r in refs):
            refs.append((m.group(1), None))
    return refs

def check(brand, dbc_path, py_files):
    print(f"\n{'=' * 60}")
    print(f"CHECKING {brand}  DBC: {dbc_path}")
    print("=" * 60)
    dbc = show(dbc_path)
    msgs = parse_dbc(dbc)
    print(f"  DBC has {len(msgs)} messages, {sum(len(m['signals']) for m in msgs.values())} signals")

    all_ok = True
    seen = set()
    for pyf in py_files:
        try:
            py = show(pyf)
        except subprocess.CalledProcessError:
            continue
        refs = extract_signals_from_py(py)
        for msg, sig in refs:
            key = (msg, sig)
            if key in seen:
                continue
            seen.add(key)
            if msg not in msgs:
                print(f"  {pyf}: MSG '{msg}' NOT IN DBC")
                all_ok = False
                continue
            if sig is not None and sig not in msgs[msg]["signals"]:
                print(f"  {pyf}: MSG '{msg}' SIG '{sig}' NOT IN DBC")
                all_ok = False
    if all_ok:
        print(f"  {len(seen)} unique message/signal refs — ALL VALID")
    return all_ok

chery_dbc = "opendbc/chery_canfd.dbc"
wuling_dbc = "opendbc/wuling_almazrs_generated.dbc"

ok = True
ok &= check("CHERY", chery_dbc, [
    "selfdrive/car/chery/carstate.py",
    "selfdrive/car/chery/carcontroller.py",
    "selfdrive/car/chery/cherycan.py",
])
ok &= check("WULING", wuling_dbc, [
    "selfdrive/car/wuling/carstate.py",
    "selfdrive/car/wuling/carcontroller.py",
    "selfdrive/car/wuling/wulingcan.py",
])

print()
print("=" * 60)
print("RESULT:", "OK" if ok else "BROKEN REFERENCES")
print("=" * 60)