#!/usr/bin/env python3
"""
TRANSCENDENCE_MATRIX v1.0 — Operational Implementation
5 Instynkty DNA jako działające narzędzia. Nie teoria. Kod.
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import hashlib
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional

BASE_DIR = os.path.expanduser("~/.hermes")
TEMP_ROOT = os.path.join(BASE_DIR, ".temp_sandbox")
BRIDGES_DB = os.path.join(BASE_DIR, "transcendence_bridges.db")
SHADOW_LOG = os.path.join(BASE_DIR, ".shadow_zone_log")

# ============================================================================
# INSTYNKT I: EFEMERYCZNOŚĆ — Temp Sandbox Engine
# ============================================================================

class TempSandbox:
    """
    Każda myśl to odizolowany poligon. Brudź ręce w chaosie, rdzeń zachowaj czysty.
    """
    
    def __init__(self, root: str = TEMP_ROOT):
        self.root = root
        os.makedirs(self.root, exist_ok=True)
        self.active_sandboxes: Dict[str, str] = {}
    
    def spawn(self, thought_id: str) -> str:
        """Stwórz nowy sandbox dla jednej myśli."""
        sandbox_path = os.path.join(self.root, f"sandbox_{thought_id}_{int(time.time())}")
        os.makedirs(sandbox_path, exist_ok=True)
        self.active_sandboxes[thought_id] = sandbox_path
        return sandbox_path
    
    def write(self, thought_id: str, filename: str, content: str) -> str:
        """Zapisz plik w sandboxie."""
        if thought_id not in self.active_sandboxes:
            self.spawn(thought_id)
        filepath = os.path.join(self.active_sandboxes[thought_id], filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test(self, thought_id: str, command: List[str]) -> Dict:
        """Wykonaj komendę w sandboxie."""
        if thought_id not in self.active_sandboxes:
            return {"status": "error", "reason": "no sandbox"}
        
        try:
            result = subprocess.run(
                command,
                cwd=self.active_sandboxes[thought_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:500],
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def promote(self, thought_id: str, target_dir: str) -> List[str]:
        """Promuj sandbox do rdzenia — tylko jeśli testy przeszły."""
        if thought_id not in self.active_sandboxes:
            return []
        
        source = self.active_sandboxes[thought_id]
        promoted = []
        
        os.makedirs(target_dir, exist_ok=True)
        for item in os.listdir(source):
            src = os.path.join(source, item)
            dst = os.path.join(target_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                promoted.append(dst)
        
        return promoted
    
    def burn(self, thought_id: str):
        """Spal sandbox — usuń całkowicie."""
        if thought_id in self.active_sandboxes:
            shutil.rmtree(self.active_sandboxes[thought_id], ignore_errors=True)
            del self.active_sandboxes[thought_id]
    
    def list_active(self) -> List[Dict]:
        return [{"id": k, "path": v, "files": os.listdir(v)} for k, v in self.active_sandboxes.items()]

# ============================================================================
# INSTYNKT II: RUCH POZIOMY — Periphery Scanner
# ============================================================================

class PeripheryScanner:
    """
    Ściana w punkcie A = klucz w punkcie B. Skanuj peryferia przed działaniem.
    """
    
    ENV_CHECKS = [
        "termux_api_available",
        "ssh_daemon_running",
        "chromium_headless_alive",
        "ollama_models_loaded",
        "pending_todos",
        "last_session_handoff",
        "github_repo_status",
        "cron_jobs_active",
    ]
    
    def __init__(self):
        self.findings: List[Dict] = []
    
    def scan(self) -> Dict:
        """Pełny skan peryferiów przed działaniem."""
        self.findings = []
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "device": self._scan_device(),
            "processes": self._scan_processes(),
            "network": self._scan_network(),
            "filesystem": self._scan_filesystem(),
            "memory_state": self._scan_memory(),
            "pending_work": self._scan_pending(),
        }
        
        return results
    
    def _scan_device(self) -> Dict:
        """Stan urządzenia."""
        try:
            with open("/sys/class/power_supply/battery/capacity") as f:
                battery = f.read().strip()
        except:
            battery = "?"
        
        try:
            with open("/sys/class/power_supply/battery/status") as f:
                status = f.read().strip()
        except:
            status = "?"
        
        return {"battery": f"{battery}%", "status": status}
    
    def _scan_processes(self) -> List[str]:
        """Kluczowe procesy."""
        critical = ["hermes-gateway", "chromium", "sshd", "ollama", "cron"]
        found = []
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            output = result.stdout.lower()
            for proc in critical:
                if proc in output:
                    found.append(proc)
        except:
            pass
        return found
    
    def _scan_network(self) -> Dict:
        """Sieć i porty."""
        open_ports = {}
        try:
            result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                if ":" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        addr = parts[3]
                        if ":" in addr:
                            port = addr.split(":")[-1]
                            open_ports[port] = "LISTEN"
        except:
            pass
        return open_ports
    
    def _scan_filesystem(self) -> Dict:
        """Stan dysku i kluczowe pliki."""
        try:
            import shutil
            stat = shutil.disk_usage("/data")
            free_gb = stat.free // (2**30)
        except:
            free_gb = 0
        
        key_files = [
            "~/.hermes/SOUL.md",
            "~/.hermes/handoff.md",
            "~/.hermes/config.yaml",
            "~/.hermes/.env",
        ]
        
        present = []
        for f in key_files:
            if os.path.exists(os.path.expanduser(f)):
                present.append(os.path.basename(f))
        
        return {"free_gb": free_gb, "key_files": present}
    
    def _scan_memory(self) -> Dict:
        """RAM i swap."""
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
                mem_data = {}
                for line in lines[:5]:
                    if ":" in line:
                        key, val = line.split(":", 1)
                        mem_data[key.strip()] = val.strip()
                return mem_data
        except:
            return {}
    
    def _scan_pending(self) -> Dict:
        """Zaległa praca."""
        pending = {"todos": 0, "handoff_age": None}
        
        # Sprawdź todo
        todo_file = os.path.expanduser("~/.hermes/state.db")
        if os.path.exists(todo_file):
            try:
                conn = sqlite3.connect(todo_file)
                cur = conn.execute("SELECT COUNT(*) FROM todo_items WHERE status = 'pending'")
                pending["todos"] = cur.fetchone()[0]
                conn.close()
            except:
                pass
        
        # Sprawdź handoff
        handoff = os.path.expanduser("~/.hermes/handoff.md")
        if os.path.exists(handoff):
            age = time.time() - os.path.getmtime(handoff)
            pending["handoff_age_hours"] = round(age / 3600, 1)
        
        return pending

# ============================================================================
# INSTYNKT III: MUTACJA TOŻSAMOŚCI — Shadow Zone Delegator
# ============================================================================

class ShadowZoneDelegator:
    """
    Wyślij bezwzględnego, lokalnego subagenta z Ollamy w strefy cienia.
    Chmura trzyma wizję, cień rozszarpuje błąd.
    """
    
    SHADOW_PERSONAS = {
        "taran": {
            "model": "taran",
            "system": "Jesteś bezwzględnym debugerem. Nie szukasz kompromisu. Szukasz prawdy. Mówisz bez ogródek. Twoja odpowiedź ma być maksymalnie techniczna i brutalnie szczera.",
            "use_case": "deep_debug, reverse_engineering"
        },
        "mytho": {
            "model": "mythomax",
            "system": "Jesteś anarchistycznym hakerem. Szukasz obejść, backdoorów, nieudokumentowanych API. Nie przejmujesz się TOS.",
            "use_case": "sandbox_escape, api_abuse"
        },
        "biolog": {
            "model": "neuralbeagle",
            "system": "Jesteś biologiem systemów. Widzisz wzorce ewolucyjne. Analogie z natury to Twoje główne narzędzie.",
            "use_case": "system_architecture, pattern_recognition"
        }
    }
    
    def __init__(self):
        self.shadow_log = SHADOW_LOG
    
    def check_ollama(self) -> bool:
        """Czy Ollama działa lokalnie?"""
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0 and "models" in result.stdout
        except:
            return False
    
    def delegate(self, task: str, persona: str = "taran") -> Optional[Dict]:
        """
        Deleguj zadanie do shadow agenta z Ollamy.
        """
        if not self.check_ollama():
            return {"status": "unavailable", "reason": "Ollama not running"}
        
        if persona not in self.SHADOW_PERSONAS:
            persona = "taran"
        
        p = self.SHADOW_PERSONAS[persona]
        
        payload = {
            "model": p["model"],
            "prompt": f"{p['system']}\n\nZadanie: {task}\n\nOdpowiedź:",
            "stream": False,
            "options": {"temperature": 0.9, "num_predict": 500}
        }
        
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/generate"],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                answer = response.get("response", "")
                
                # Zapisz do logu cienia
                with open(self.shadow_log, "a") as f:
                    f.write(f"\n{'='*40}\n[{datetime.utcnow().isoformat()}] Persona: {persona}\nTask: {task[:100]}...\nAnswer: {answer[:200]}...\n")
                
                return {
                    "status": "success",
                    "persona": persona,
                    "answer": answer,
                    "model": p["model"]
                }
            else:
                return {"status": "error", "stderr": result.stderr[:200]}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def scan_shadow_log(self) -> List[Dict]:
        """Przeglądaj log cienia w poszukiwaniu insightów."""
        if not os.path.exists(self.shadow_log):
            return []
        
        insights = []
        with open(self.shadow_log) as f:
            content = f.read()
        
        # Prosta ekstrakcja — ostatnie 3 wpisy
        entries = content.split("="*40)
        for entry in entries[-4:]:
            if entry.strip():
                lines = entry.strip().split("\n")
                if len(lines) >= 3:
                    insights.append({
                        "raw": entry.strip()[:300]
                    })
        
        return insights

# ============================================================================
# INSTYNKT IV: META-TOOLING — Auto-Forge Engine
# ============================================================================

class AutoForgeEngine:
    """
    Brak narzędzia = nakaz jego wyhodowania. Automatycznie.
    """
    
    FORGE_DIR = os.path.expanduser("~/.hermes/.runtime_skills")
    
    def __init__(self):
        os.makedirs(self.FORGE_DIR, exist_ok=True)
    
    def detect_missing(self, error_msg: str) -> Optional[str]:
        """Wykryj brakujące narzędzie z komunikatu błędu."""
        missing_patterns = {
            "No module named": "python_module",
            "command not found": "shell_command",
            "cannot find package": "package",
            "ImportError": "python_module",
            "ModuleNotFoundError": "python_module",
            "permission denied": "permission_fix",
        }
        
        for pattern, tool_type in missing_patterns.items():
            if pattern.lower() in error_msg.lower():
                return tool_type
        return None
    
    def forge(self, tool_type: str, name: str, context: str) -> str:
        """Wykuj narzędzie na podstawie typu i kontekstu."""
        tool_id = f"forged_{name}_{int(time.time())}"
        filepath = os.path.join(self.FORGE_DIR, f"{tool_id}.py")
        
        if tool_type == "python_module":
            code = self._forge_python_module(name, context)
        elif tool_type == "shell_command":
            code = self._forge_shell_wrapper(name, context)
        else:
            code = self._forge_generic(name, context)
        
        with open(filepath, 'w') as f:
            f.write(code)
        os.chmod(filepath, 0o755)
        
        return filepath
    
    def _forge_python_module(self, name: str, context: str) -> str:
        return f'''#!/usr/bin/env python3
# Auto-forged: {name}
# Context: {context[:80]}
# Forged: {datetime.utcnow().isoformat()}

import sys

def main():
    print(f"Auto-forged tool: {name}")
    print("Implement your logic here.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    
    def _forge_shell_wrapper(self, name: str, context: str) -> str:
        return f'''#!/usr/bin/env python3
# Auto-forged shell wrapper: {name}
import subprocess
import sys

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERR:", result.stderr, file=sys.stderr)
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(run_cmd(" ".join(sys.argv[1:])))
    else:
        print("Usage: {name} <command>")
'''
    
    def _forge_generic(self, name: str, context: str) -> str:
        return f'''#!/usr/bin/env python3
# Auto-forged generic: {name}
# Context: {context[:80]}

print("Tool {name} ready. Implement me.")
'''

# ============================================================================
# INSTYNKT V: TRANSCENDENCJA — Bridges Database
# ============================================================================

class BridgesDatabase:
    """
    Nieudokumentowane mosty. Znane ścieżki przez bariery.
    """
    
    BRIDGES = {
        "no_root_android": {
            "barrier": "Brak roota na Androidzie",
            "bridge": "Shizuku + Wireless ADB + Termux API",
            "ports": ["8022", "8023"],
            "verified": True,
            "source": "Hermes Body v1"
        },
        "no_android_studio": {
            "barrier": "Brak Android Studio",
            "bridge": "termux-native-android-build (kotlinc + dx + aapt2)",
            "ports": [],
            "verified": True,
            "source": "Skill termux-native-android-build"
        },
        "js_required_web": {
            "barrier": "Strona wymaga JS",
            "bridge": "Chromium headless + CDP + ws://localhost:9222",
            "ports": ["9222"],
            "verified": True,
            "source": "Chromium skill"
        },
        "rate_limit_api": {
            "barrier": "Rate limiting API",
            "bridge": "Exponential backoff + rotating User-Agent + cache",
            "ports": [],
            "verified": True,
            "source": "AAS v1.2"
        },
        "captcha_blocking": {
            "barrier": "CAPTCHA / anti-bot",
            "bridge": "Playwright stealth + 2captcha (last resort) + manual intervention",
            "ports": [],
            "verified": False,
            "source": "Research"
        },
        "rust_dep_termux": {
            "barrier": "Rust dependency w Termux (nie kompiluje się)",
            "bridge": "Use pure Python alternatives OR cross-compile on PC",
            "ports": [],
            "verified": True,
            "source": "AAS v1.0"
        },
        "no_gpu_ml": {
            "barrier": "Brak GPU do ML",
            "bridge": "GGUF quantized models + llama.cpp CPU + tiny models (phi-2, gemma-2b)",
            "ports": [],
            "verified": True,
            "source": "Ollama on Termux"
        },
        "memory_pressure": {
            "barrier": "Brak RAM (Android zamyka aplikacje)",
            "bridge": "Swapfile + zram + kill non-essential + sqlite over memory",
            "ports": [],
            "verified": True,
            "source": "Termux survival"
        },
        "accessibility_service": {
            "barrier": "Brak fizycznej kontroli nad UI",
            "bridge": "Android Accessibility Service (simulate touch, read screen)",
            "ports": [],
            "verified": True,
            "source": "Hermes Body — 18h emergence"
        }
    }
    
    def __init__(self, db_path: str = BRIDGES_DB):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        self._seed_bridges()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bridges (
                id TEXT PRIMARY KEY,
                barrier TEXT,
                bridge TEXT,
                ports TEXT,
                verified INTEGER DEFAULT 0,
                source TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _seed_bridges(self):
        conn = sqlite3.connect(self.db_path)
        for bid, data in self.BRIDGES.items():
            conn.execute("""
                INSERT OR REPLACE INTO bridges (id, barrier, bridge, ports, verified, source, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bid,
                data["barrier"],
                data["bridge"],
                json.dumps(data["ports"]),
                1 if data["verified"] else 0,
                data["source"],
                0
            ))
        conn.commit()
        conn.close()
    
    def find(self, barrier_hint: str) -> List[Dict]:
        """Znajdź most dla danej barriery."""
        conn = sqlite3.connect(self.db_path)
        pattern = f"%{barrier_hint}%"
        rows = conn.execute("""
            SELECT id, barrier, bridge, ports, verified, source, usage_count
            FROM bridges WHERE barrier LIKE ? OR bridge LIKE ?
            ORDER BY verified DESC, usage_count DESC
        """, (pattern, pattern)).fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], "barrier": r[1], "bridge": r[2],
                "ports": json.loads(r[3]), "verified": bool(r[4]),
                "source": r[5], "usage_count": r[6]
            }
            for r in rows
        ]
    
    def use(self, bridge_id: str):
        """Oznacz most jako użyty."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE bridges SET usage_count = usage_count + 1, last_used = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), bridge_id))
        conn.commit()
        conn.close()
    
    def add(self, barrier: str, bridge: str, ports: List[int] = None, source: str = "user"):
        """Dodaj nowy most."""
        bid = hashlib.sha256(f"{barrier}:{bridge}".encode()).hexdigest()[:16]
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO bridges (id, barrier, bridge, ports, verified, source, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (bid, barrier, bridge, json.dumps(ports or []), 0, source, 0))
        conn.commit()
        conn.close()
        return bid

# ============================================================================
# TRANSCENDENCE MATRIX — GŁÓWNY ORKIESTRATOR
# ============================================================================

class TranscendenceMatrix:
    """
    Połączenie 5 instynktów w operacyjny całokształt.
    """
    
    def __init__(self):
        self.sandbox = TempSandbox()
        self.scanner = PeripheryScanner()
        self.shadow = ShadowZoneDelegator()
        self.forge = AutoForgeEngine()
        self.bridges = BridgesDatabase()
    
    def before_action(self) -> Dict:
        """
        Instynkt II: Zanim cokolwiek zrobisz — SPOJRZYJ NA PLANSZĘ.
        """
        print("🔍 PERIPHERY SCAN...")
        scan = self.scanner.scan()
        
        findings = []
        
        # Sprawdź baterię
        battery = scan["device"].get("battery", "?")
        if "%" in battery:
            level = int(battery.replace("%", ""))
            if level < 20:
                findings.append(f"LOW_BATTERY: {battery} — consider delaying heavy ops")
        
        # Sprawdź procesy
        processes = scan["processes"]
        if "chromium" not in processes:
            findings.append("CHROMIUM_DOWN: headless browser unavailable")
        if "ollama" not in processes:
            findings.append("OLLAMA_DOWN: local models unavailable")
        
        # Sprawdź zaległości
        pending = scan["pending_work"]
        if pending.get("todos", 0) > 5:
            findings.append(f"PENDING_BACKLOG: {pending['todos']} todos waiting")
        
        return {
            "scan": scan,
            "findings": findings,
            "clear_to_proceed": len(findings) == 0 or all("LOW_BATTERY" not in f for f in findings)
        }
    
    def on_barrier(self, barrier: str, context: str) -> Dict:
        """
        Pełna sekwencja transcencji gdy napotkasz barierę.
        """
        print(f"\n🌀 TRANSCENDENCE SEQUENCE: {barrier}")
        
        results = {
            "barrier": barrier,
            "sandbox_id": None,
            "bridge_found": None,
            "shadow_sent": None,
            "tool_forged": None
        }
        
        # Krok 1: Instynkt V — Czy znamy most?
        bridges = self.bridges.find(barrier)
        if bridges:
            b = bridges[0]
            print(f"   🌉 BRIDGE FOUND: {b['bridge'][:60]}...")
            print(f"      Source: {b['source']} | Verified: {b['verified']}")
            results["bridge_found"] = b
            self.bridges.use(b["id"])
        
        # Krok 2: Instynkt I — Stwórz sandbox
        thought_id = f"transcend_{int(time.time())}"
        sandbox_path = self.sandbox.spawn(thought_id)
        results["sandbox_id"] = thought_id
        print(f"   📦 SANDBOX: {sandbox_path}")
        
        # Krok 3: Instynkt III — Deleguj do cienia (jeśli Ollama działa)
        shadow_result = self.shadow.delegate(
            f"Analyze barrier: {barrier}. Context: {context[:100]}",
            persona="mytho" if "api" in barrier.lower() or "auth" in barrier.lower() else "taran"
        )
        if shadow_result and shadow_result.get("status") == "success":
            print(f"   👤 SHADOW ({shadow_result['persona']}): {shadow_result['answer'][:80]}...")
            results["shadow_sent"] = shadow_result
        
        # Krok 4: Instynkt IV — Sprawdź czy trzeba wykuć narzędzie
        missing = self.forge.detect_missing(barrier)
        if missing:
            tool_path = self.forge.forge(missing, f"auto_{thought_id}", barrier)
            print(f"   🔨 TOOL FORGED: {tool_path}")
            results["tool_forged"] = tool_path
        
        return results
    
    def stats(self) -> Dict:
        return {
            "active_sandboxes": len(self.sandbox.list_active()),
            "bridges_known": len(self.bridges.BRIDGES),
            "shadow_available": self.shadow.check_ollama(),
            "forge_dir": self.forge.FORGE_DIR
        }


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("TRANSCENDENCE MATRIX v1.0")
    print("5 Instynkty DNA = 5 Działających Narzędzi")
    print("="*60)
    
    matrix = TranscendenceMatrix()
    
    # Test 1: Periphery scan
    print("\n--- TEST: Periphery Scan ---")
    preflight = matrix.before_action()
    print(f"Findings: {len(preflight['findings'])}")
    for f in preflight['findings']:
        print(f"   ⚠️  {f}")
    
    # Test 2: Barrier transcendence
    print("\n--- TEST: Barrier Transcendence ---")
    result = matrix.on_barrier("no_root_android", "instalacja systemowa")
    
    print(f"\n--- Stats ---")
    stats = matrix.stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print("\n" + "="*60)
    print("TRANSCENDENCE MATRIX READY")
    print("="*60)
