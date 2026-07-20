#!/usr/bin/env python3
"""Vital Guardian — system health monitor for Hermes A52"""

import os
import sys
import shutil
import subprocess
import time
import json
from datetime import datetime, timedelta

HOME = os.path.expanduser("~/.hermes")
LOG_FILE = f"{HOME}/logs/vital-guardian.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def get_disk_usage():
    stat = shutil.disk_usage("/data")
    used_percent = (stat.used / stat.total) * 100
    return {
        "total": stat.total // (1024**3),
        "used": stat.used // (1024**3),
        "free": stat.free // (1024**3),
        "percent": used_percent
    }

def get_memory_usage():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        total = int(lines[0].split()[1]) // 1024  # MB
        available = int(lines[2].split()[1]) // 1024  # MB
        used = total - available
        return {
            "total_mb": total,
            "used_mb": used,
            "available_mb": available,
            "percent": (used / total) * 100
        }
    except:
        return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "percent": 0}

def get_battery():
    try:
        result = subprocess.run(["termux-battery-status"], 
                              capture_output=True, text=True, timeout=5)
        return json.loads(result.stdout)
    except:
        return {"status": "UNKNOWN", "percentage": -1}

def check_gateway():
    try:
        result = subprocess.run(["pgrep", "-f", "hermes"], 
                              capture_output=True, text=True, timeout=5)
        return len(result.stdout.strip().split("\n"))
    except:
        return 0

def check_backup_age():
    try:
        latest = max(
            [f for f in os.listdir(f"{HOME}/backups") if f.endswith(".tar.gz")],
            key=lambda x: os.path.getmtime(f"{HOME}/backups/{x}")
        )
        mtime = os.path.getmtime(f"{HOME}/backups/{latest}")
        age_hours = (time.time() - mtime) / 3600
        return age_hours
    except:
        return 999

def clean_disk():
    """Auto-czyszczenie gdy dysk > 90%"""
    cleaned = 0
    
    # 1. Stare sessions
    sessions_dir = f"{HOME}/sessions"
    if os.path.exists(sessions_dir):
        for root, dirs, files in os.walk(sessions_dir):
            for f in files:
                path = os.path.join(root, f)
                try:
                    if os.path.getmtime(path) < time.time() - (3 * 86400):
                        os.remove(path)
                        cleaned += 1
                except: pass
    
    # 2. Pip cache
    pip_cache = os.path.expanduser("~/.cache/pip")
    if os.path.exists(pip_cache):
        shutil.rmtree(pip_cache)
        log(f"Cleaned pip cache")
    
    # 3. Zepsute bazy
    for f in os.listdir(HOME):
        if "corrupted" in f or "BROKEN" in f:
            try:
                os.remove(f"{HOME}/{f}")
                log(f"Removed corrupted DB: {f}")
            except: pass
    
    # 4. Stare backupy
    backups = sorted(
        [f"{HOME}/backups/{f}" for f in os.listdir(f"{HOME}/backups") if f.endswith(".tar.gz")],
        key=os.path.getmtime
    )
    while len(backups) > 5:
        try:
            os.remove(backups.pop(0))
            log(f"Removed old backup")
        except: pass
    
    # 5. State snapshots
    snapshots = sorted(
        [f"{HOME}/state-snapshots/{f}" for f in os.listdir(f"{HOME}/state-snapshots") if f.endswith(".db")],
        key=os.path.getmtime
    )
    while len(snapshots) > 10:
        try:
            os.remove(snapshots.pop(0))
            log(f"Removed old snapshot")
        except: pass
    
    # 6. Tmp
    tmp_dir = os.path.expanduser("~/tmp")
    if os.path.exists(tmp_dir):
        for f in os.listdir(tmp_dir):
            path = os.path.join(tmp_dir, f)
            try:
                if os.path.getmtime(path) < time.time() - (7 * 86400):
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                    cleaned += 1
            except: pass
    
    return cleaned

def scan():
    """Pełny skan systemu"""
    log("=== VITAL SCAN ===")
    
    disk = get_disk_usage()
    log(f"Disk: {disk['used']:.1f}GB / {disk['total']:.1f}GB ({disk['percent']:.1f}%)")
    
    mem = get_memory_usage()
    log(f"RAM: {mem['used_mb']:.0f}MB / {mem['total_mb']:.0f}MB ({mem['percent']:.1f}%)")
    
    bat = get_battery()
    log(f"Battery: {bat.get('percentage', -1)}% ({bat.get('status', 'UNKNOWN')})")
    
    gw = check_gateway()
    log(f"Gateway processes: {gw}")
    
    backup_age = check_backup_age()
    log(f"Backup age: {backup_age:.1f}h")
    
    # Status
    status = "OK"
    alerts = []
    
    if disk['percent'] > 95:
        status = "DEAD"
        alerts.append(f"DISK CRITICAL: {disk['percent']:.1f}%")
    elif disk['percent'] > 90:
        status = "CRITICAL"
        alerts.append(f"Disk critical: {disk['percent']:.1f}%")
    elif disk['percent'] > 85:
        status = "WARNING"
        alerts.append(f"Disk warning: {disk['percent']:.1f}%")
    
    if mem['percent'] > 95:
        alerts.append(f"RAM critical: {mem['percent']:.1f}%")
        status = max(status, "CRITICAL", key=lambda x: {"OK": 0, "WARNING": 1, "CRITICAL": 2, "DEAD": 3}.get(x, 0))
    
    if bat.get('percentage', 100) < 15:
        alerts.append(f"Battery critical: {bat['percentage']}%")
    elif bat.get('percentage', 100) < 30:
        alerts.append(f"Battery low: {bat['percentage']}%")
    
    if gw == 0:
        alerts.append("Gateway DEAD")
        status = "DEAD"
    elif gw < 2:
        alerts.append("Gateway weak")
    
    if backup_age > 12:
        alerts.append(f"Backup stale: {backup_age:.1f}h")
    elif backup_age > 6:
        alerts.append(f"Backup old: {backup_age:.1f}h")
    
    log(f"Status: {status}")
    if alerts:
        for a in alerts:
            log(f"  ALERT: {a}")
    
    # Auto-clean jeśli krytyczny dysk
    if disk['percent'] > 90:
        log("Auto-cleaning...")
        cleaned = clean_disk()
        log(f"Auto-cleaned {cleaned} items")
        # Skan ponownie
        disk = get_disk_usage()
        log(f"Disk after clean: {disk['percent']:.1f}%")
    
    log("=== END SCAN ===")
    return status, alerts

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        status, alerts = scan()
        sys.exit(0 if status in ["OK", "WARNING"] else 1)
    elif cmd == "clean":
        clean_disk()
    elif cmd == "watch":
        while True:
            scan()
            time.sleep(300)  # co 5 min
    else:
        print("Usage: vital-guardian.py [scan|clean|watch]")
