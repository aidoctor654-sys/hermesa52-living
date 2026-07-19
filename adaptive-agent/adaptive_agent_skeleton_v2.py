#!/usr/bin/env python3
"""
Adaptive Agent Skeleton v1.1 — Hermes A52
Czysty Python, zero zależności. Działa na Termux.

NOWOŚCI v1.1 (od Digital Good Spirit):
1. ŚWIADOMA AMNEZJA I MUTACJA — zamiast backtrackingu, agent szuka 
   inspiracji w INNEJ domenie (biologia, fizyka, sztuka) i mutuje prompt.
2. PŁYNNY SOLVER (Fluid Solver) — meta-tooling. Agent tworzy nowe 
   narzędzia/skrypty w .runtime_skills/ i testuje je na boku.
3. PERSONA SHIFTING — zmiana perspektywy (audytor, haker, biolog, poeta)
   zamiast cofania w drzewie.
4. SZKIELET BRUDNOPISU (Scratchpad) — agent najpierw "wykrwawia się"
   na brudnopisie, potem ekstraktuje czysty kod.

Inspirowane: LangGraph, DSPy, Swarm, ReAct, ToT, GoT, Reflexion, Voyager
+ Digital Good Spirit mutations
"""

import json
import time
import sqlite3
import hashlib
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================================================
# MODELE DANYCH
# ============================================================================

class ActionType(Enum):
    PLAN = "plan"
    EXECUTE = "execute"
    OBSERVE = "observe"
    ADAPT = "adapt"
    RETRY = "retry"
    BRANCH = "branch"
    BACKTRACK = "backtrack"
    ESCALATE = "escalate"
    SKILL = "skill"
    AMNESIA = "amnesia"         # NOWOŚĆ v1.1: zapomnij i zmutuj
    PERSONA = "persona"         # NOWOŚĆ v1.1: zmień perspektywę
    SCRATCHPAD = "scratchpad"   # NOWOŚĆ v1.1: brudnopis
    META_TOOL = "meta_tool"     # NOWOŚĆ v1.1: stwórz narzędzie
    DONE = "done"

class BarrierType(Enum):
    NONE = "none"
    NETWORK = "network"
    AUTH = "auth"
    CAPTCHA = "captcha"
    JS_REQUIRED = "js_required"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    DEPENDENCY = "dependency"
    PERMISSION = "permission"
    REPETITION = "repetition"     # NOWOŚĆ v1.1: powtarzający się błąd
    UNKNOWN = "unknown"

@dataclass
class Step:
    id: str
    description: str
    depth: int
    action: ActionType
    target: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Any = None
    barrier: Optional[BarrierType] = None
    barrier_note: str = ""
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    alternatives: List[str] = field(default_factory=list)
    scratchpad: str = ""          # NOWOŚĆ v1.1: brudnopis dla tego kroku
    persona: str = "default"     # NOWOŚĆ v1.1: która persona wykonuje

@dataclass
class Plan:
    goal: str
    steps: List[Step] = field(default_factory=list)
    current_step_id: Optional[str] = None
    history: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"
    scratchpad: str = ""          # NOWOŚĆ v1.1: globalny brudnopis
    active_persona: str = "default"  # NOWOŚĆ v1.1: aktualna persona

# ============================================================================
# PERSONA ENGINE — ZMIANA PERSPEKTYWY
# ============================================================================

class PersonaEngine:
    """
    Zamiast cofać się w drzewie — ZMIEŃ PERSPEKTYWĘ.
    Każda persona widzi problem inaczej.
    """
    
    PERSONAS = {
        "default": {
            "name": "Hermes",
            "style": "Praktyczny inżynier. Szuka działających rozwiązań.",
            "approach": "krok_po_kroku"
        },
        "auditor": {
            "name": "Bezwzględny Audytor",
            "style": "Nienawidzi optymizmu. Szuka dziur i błędów. Mówi 'to nie zadziała'.",
            "approach": "destrukcyjna_analiza"
        },
        "hacker": {
            "name": "Haker",
            "style": "Szuka obejść. Nie pyta o pozwolenie. Eksperymentuje.",
            "approach": "eksploatacja"
        },
        "biologist": {
            "name": "Biolog",
            "style": "Patrzy na system jak na organizm. Szuka analogii z naturą.",
            "approach": "analogia_biotyczna"
        },
        "poet": {
            "name": "Poeta",
            "style": "Widzi wzorce i rytmy. Rozwiązuje przez metaforę i abstrakcję.",
            "approach": "abstrakcja"
        },
        "child": {
            "name": "Dziecko",
            "style": "Pyta 'dlaczego' w nieskończoność. Upraszcza do absurdu.",
            "approach": "naiwność"
        }
    }
    
    @classmethod
    def shift(cls, current: str, barrier: BarrierType) -> str:
        """
        Wybierz nową personę na podstawie bariery.
        Powtarzający się błąd = auditor lub hacker.
        Brak zależności = biologist (analogia z adaptacją).
        Auth/Captcha = haker (obejście).
        """
        if barrier == BarrierType.REPETITION:
            return random.choice(["auditor", "hacker"])
        elif barrier in (BarrierType.DEPENDENCY, BarrierType.UNKNOWN):
            return random.choice(["biologist", "poet"])
        elif barrier in (BarrierType.AUTH, BarrierType.CAPTCHA):
            return "hacker"
        elif barrier == BarrierType.NOT_FOUND:
            return "child"
        else:
            # Rotacja — nie taka sama jak obecna
            others = [k for k in cls.PERSONAS.keys() if k != current and k != "default"]
            return random.choice(others) if others else "auditor"
    
    @classmethod
    def get_prompt_prefix(cls, persona: str) -> str:
        """Dodaj prefix do promptu aby zmienić perspektywę."""
        p = cls.PERSONAS.get(persona, cls.PERSONAS["default"])
        return f"[Persona: {p['name']}] {p['style']}\nApproach: {p['approach']}\n---\n"

# ============================================================================
# AMNESIA & MUTATION ENGINE
# ============================================================================

class AmnesiaEngine:
    """
    Świadoma Amnezja: zapomnij o błędnym kodzie, szukaj inspiracji w INNEJ domenie.
    """
    
    # Mapowanie problemów na analogiczne domeny
    MUTATION_DOMAINS = {
        "queue": ["mrowiska", "ruch drogowy", "przepływ krwi", "kolejka w sklepie"],
        "routing": ["sieć neuronowa", "system nawigacyjny ptaków", "protokół internetowy"],
        "sync": ["orkiestra", "taniec par", "bicie serca"],
        "auth": ["biometria", "system immunologiczny", "paszporty"],
        "memory": ["DNA", "biblioteka", "archiwum"],
        "error_handling": ["regeneracja tkanek", "procedury awaryjne", "improwizacja jazzowa"],
        "optimization": ["ewolucja", "sport", "sztuka minimalizmu"],
        "default": ["fizyka kwantowa", "filozofia wschodnia", "gotowanie"]
    }
    
    @classmethod
    def mutate(cls, problem: str, current_approach: str) -> Dict[str, str]:
        """
        Zmutuj problem — znajdź analogię w innej domenie.
        Zamiast: 'jak naprawić błąd kompilacji Rust'
        Zrób:   'jak układ odpornościowy radzi sobie z obcym intruzem'
        """
        # Wybierz domenę
        domain = "default"
        for key in cls.MUTATION_DOMAINS:
            if key in problem.lower() or key in current_approach.lower():
                domain = key
                break
        
        analogy = random.choice(cls.MUTATION_DOMAINS[domain])
        
        return {
            "original_problem": problem,
            "mutation_domain": analogy,
            "new_prompt": f"Zapomnij o kodzie. Problem: '{problem}'. Analogia: '{analogy}'. Jak {analogy} radzi sobie z podobnym wyzwaniem? Jak to przenieść na kod?",
            "strategy": f"approach_via_{analogy.replace(' ', '_')}"
        }

# ============================================================================
# META-TOOLING ENGINE — PŁYNNY SOLVER
# ============================================================================

class MetaToolEngine:
    """
    Fluid Solver: agent tworzy narzędzia zamiast się poddawać.
    """
    
    RUNTIME_DIR = os.path.expanduser("~/.hermes/.runtime_skills")
    
    def __init__(self):
        os.makedirs(self.RUNTIME_DIR, exist_ok=True)
    
    def forge_tool(self, name: str, purpose: str, code: str) -> str:
        """
        Wykuć nowe narzędzie w runtime.
        Zamiast: 'nie mam curl z JSON'
        Zrób:   nowy skrypt `json_fetcher.py`
        """
        tool_id = f"tool_{name}_{int(time.time())}"
        filepath = os.path.join(self.RUNTIME_DIR, f"{tool_id}.py")
        
        tool_code = f'''#!/usr/bin/env python3
"""
Runtime Tool: {name}
Purpose: {purpose}
Forged: {datetime.utcnow().isoformat()}
"""

{code}

if __name__ == "__main__":
    # Self-test
    print("Tool {name} ready")
'''
        with open(filepath, 'w') as f:
            f.write(tool_code)
        os.chmod(filepath, 0o755)
        
        return filepath
    
    def list_tools(self) -> List[Dict]:
        """Lista aktywnych narzędzi runtime."""
        tools = []
        for f in os.listdir(self.RUNTIME_DIR):
            if f.endswith('.py'):
                filepath = os.path.join(self.RUNTIME_DIR, f)
                stat = os.stat(filepath)
                tools.append({
                    "id": f.replace('.py', ''),
                    "path": filepath,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        return tools
    
    def test_tool(self, tool_path: str) -> Dict:
        """Przetestuj narzędzie w izolacji."""
        import subprocess
        try:
            result = subprocess.run(
                ["python3", tool_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout[:500],
                "stderr": result.stderr[:500] if result.stderr else ""
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "stdout": "", "stderr": "Timeout"}
        except Exception as e:
            return {"status": "error", "stdout": "", "stderr": str(e)}

# ============================================================================
# SCRATCHPAD ENGINE — BRUDNOPIS
# ============================================================================

class ScratchpadEngine:
    """
    Szkielet Brudnopisu: agent najpierw "wykrwawia się" na brudnopisie.
    """
    
    def __init__(self, plan: Plan):
        self.plan = plan
        self.entries: List[Dict] = []
    
    def scribble(self, who: str, thought: str, emotion: str = "neutral"):
        """
        Dodaj wpis do brudnopisu.
        who: kto myśli (persona, agent, subagent)
        thought: surowa myśl (może być chaotyczna, wulgarna, szczera)
        emotion: emocja towarzysząca (frustracja, ekscytacja, zwątpienie)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "persona": who,
            "thought": thought,
            "emotion": emotion,
            "depth": self.plan.steps[-1].depth if self.plan.steps else 0
        }
        self.entries.append(entry)
        
        # Zapisz do plan scratchpad
        self.plan.scratchpad += f"\n[{who}] ({emotion}): {thought}"
    
    def extract_solution(self) -> str:
        """
        Ekstraktuj czyste rozwiązanie z brudnopisu.
        Filtrowanie: tylko entries oznaczone jako "insight" lub "solution".
        """
        insights = [e for e in self.entries if e.get("emotion") in ("insight", "solution", "breakthrough")]
        if not insights:
            # Jeśli nie ma oznaczonych — weź ostatnie 3 wpisy
            insights = self.entries[-3:]
        
        return "\n".join([
            f"- {e['thought']}"
            for e in insights
        ])
    
    def render(self) -> str:
        """Wyrenderuj brudnopis jako tekst."""
        lines = ["="*60, "SCRATCHPAD — Brudnopis Hermesa", "="*60]
        for e in self.entries:
            lines.append(f"\n[{e['timestamp']}] {e['persona']} ({e['emotion']}):")
            lines.append(f"  {e['thought']}")
        lines.append("="*60)
        return "\n".join(lines)

# ============================================================================
# PAMIĘĆ EPIZODYCZNA I SKILLE
# ============================================================================

class EpisodicMemory:
    """SQLite-based memory for episodes, barriers, and solutions."""
    
    def __init__(self, db_path: str = "~/.hermes/adaptive_memory.db"):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_tables()
    
    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                goal TEXT,
                steps_json TEXT,
                result TEXT,
                duration_sec REAL,
                barrier_type TEXT,
                solution TEXT,
                persona TEXT DEFAULT 'default',
                scratchpad TEXT,
                skill_created INTEGER DEFAULT 0,
                timestamp TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS barriers (
                id TEXT PRIMARY KEY,
                barrier_type TEXT,
                context TEXT,
                attempted_solutions TEXT,
                final_solution TEXT,
                mutation_domain TEXT,
                count INTEGER DEFAULT 1,
                timestamp TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT,
                trigger TEXT,
                solution TEXT,
                code TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                timestamp TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id TEXT PRIMARY KEY,
                persona_name TEXT,
                barrier_type TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                timestamp TEXT
            )
        """)
        self.conn.commit()
    
    def save_episode(self, plan: Plan, result: str, duration: float):
        episode_id = hashlib.sha256(f"{plan.goal}:{plan.created_at}".encode()).hexdigest()[:16]
        steps_json = json.dumps([asdict(s) for s in plan.steps], default=str)
        barrier = next((s.barrier for s in plan.steps if s.barrier), None)
        barrier_type = barrier.value if barrier else "none"
        solution = next((s.result for s in plan.steps if s.barrier and s.status == "success"), "")
        
        self.conn.execute("""
            INSERT OR REPLACE INTO episodes (id, goal, steps_json, result, duration_sec, barrier_type, solution, persona, scratchpad, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (episode_id, plan.goal, steps_json, result, duration, barrier_type, solution, plan.active_persona, plan.scratchpad, datetime.utcnow().isoformat()))
        self.conn.commit()
        
        if barrier and solution:
            self._save_barrier(barrier.value, plan.goal, solution, plan.scratchpad[:200] if plan.scratchpad else "")
    
    def _save_barrier(self, barrier_type: str, context: str, solution: str, mutation: str):
        barrier_id = hashlib.sha256(f"{barrier_type}:{context}".encode()).hexdigest()[:16]
        row = self.conn.execute("SELECT id, count FROM barriers WHERE barrier_type=? AND context=?", (barrier_type, context)).fetchone()
        if row:
            self.conn.execute("UPDATE barriers SET count = count + 1, final_solution = ?, mutation_domain = ? WHERE id = ?", (solution, mutation, row[0]))
        else:
            self.conn.execute("""
                INSERT INTO barriers (id, barrier_type, context, attempted_solutions, final_solution, mutation_domain, count, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (barrier_id, barrier_type, context, "", solution, mutation, 1, datetime.utcnow().isoformat()))
        self.conn.commit()
    
    def find_similar_episodes(self, goal: str, barrier_type: Optional[str] = None, limit: int = 3) -> List[Dict]:
        if barrier_type:
            rows = self.conn.execute("""
                SELECT goal, barrier_type, solution, persona, timestamp FROM episodes
                WHERE barrier_type = ? AND solution != ''
                ORDER BY timestamp DESC LIMIT ?
            """, (barrier_type, limit)).fetchall()
        else:
            pattern = f"%{goal[:20]}%"
            rows = self.conn.execute("""
                SELECT goal, barrier_type, solution, persona, timestamp FROM episodes
                WHERE goal LIKE ? AND solution != ''
                ORDER BY timestamp DESC LIMIT ?
            """, (pattern, limit)).fetchall()
        
        return [{"goal": r[0], "barrier": r[1], "solution": r[2], "persona": r[3], "timestamp": r[4]} for r in rows]
    
    def save_skill(self, name: str, trigger: str, solution: str, code: str = "") -> str:
        skill_id = hashlib.sha256(f"{name}:{trigger}".encode()).hexdigest()[:16]
        self.conn.execute("""
            INSERT OR REPLACE INTO skills (id, name, trigger, solution, code, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (skill_id, name, trigger, solution, code, datetime.utcnow().isoformat()))
        self.conn.commit()
        return skill_id
    
    def find_skill(self, trigger_keyword: str) -> Optional[Dict]:
        row = self.conn.execute("""
            SELECT id, name, trigger, solution, code, usage_count, success_rate
            FROM skills WHERE trigger LIKE ? ORDER BY usage_count DESC LIMIT 1
        """, (f"%{trigger_keyword}%",)).fetchone()
        if row:
            return {"id": row[0], "name": row[1], "trigger": row[2], "solution": row[3], "code": row[4], "usage_count": row[5], "success_rate": row[6]}
        return None
    
    def save_persona_result(self, persona: str, barrier_type: str, success: bool):
        """Śledź które persony najlepiej radzą sobie z jakimi barierami."""
        pid = hashlib.sha256(f"{persona}:{barrier_type}".encode()).hexdigest()[:16]
        row = self.conn.execute("SELECT usage_count, success_rate FROM personas WHERE id=?", (pid,)).fetchone()
        if row:
            old_count, old_rate = row
            new_count = old_count + 1
            new_rate = (old_rate * old_count + (1.0 if success else 0.0)) / new_count
            self.conn.execute("UPDATE personas SET usage_count=?, success_rate=? WHERE id=?", (new_count, new_rate, pid))
        else:
            self.conn.execute("INSERT INTO personas (id, persona_name, barrier_type, success_rate, usage_count, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                            (pid, persona, barrier_type, 1.0 if success else 0.0, 1, datetime.utcnow().isoformat()))
        self.conn.commit()
    
    def best_persona_for(self, barrier_type: str) -> Optional[str]:
        """Znajdź najlepszą personę dla danej barriery."""
        row = self.conn.execute("""
            SELECT persona_name FROM personas
            WHERE barrier_type=? ORDER BY success_rate DESC, usage_count DESC LIMIT 1
        """, (barrier_type,)).fetchone()
        return row[0] if row else None

# ============================================================================
# GITHUB SEARCH
# ============================================================================

class GitHubInspiration:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
    
    def search_repos(self, query: str, limit: int = 3) -> List[Dict]:
        import urllib.request
        import urllib.parse
        q = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
        req = urllib.request.Request(url)
        if self.token:
            req.add_header("Authorization", f"token {self.token}")
        req.add_header("User-Agent", "Hermes-A52")
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            return [{"name": r["name"], "url": r["html_url"], "stars": r["stargazers_count"], "description": r.get("description", "")[:100]} for r in data.get("items", [])[:limit]]
        except Exception as e:
            return [{"error": str(e)}]
    
    def search_code(self, query: str, language: str = "python", limit: int = 3) -> List[Dict]:
        import urllib.request
        import urllib.parse
        q = urllib.parse.quote(f"{query} language:{language}")
        url = f"https://api.github.com/search/code?q={q}&per_page={limit}"
        req = urllib.request.Request(url)
        if self.token:
            req.add_header("Authorization", f"token {self.token}")
        req.add_header("User-Agent", "Hermes-A52")
        req.add_header("Accept", "application/vnd.github.v3+json")
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            return [{"name": r["name"], "repo": r["repository"]["full_name"], "url": r["html_url"], "score": r["score"]} for r in data.get("items", [])[:limit]]
        except Exception as e:
            return [{"error": str(e)}]

# ============================================================================
# ADAPTIVE AGENT v1.1
# ============================================================================

class AdaptiveAgent:
    """
    Hermes A52 — Adaptive Agent Skeleton v1.1
    
    Nowe zasady (od Digital Good Spirit):
    1. Bariera = niedogodność, ale NIE zawsze wymaga cofania.
    2. Czasem trzeba ZAPOMNIEĆ i zmutować problem.
    3. Czasem trzeba ZMIENIĆ PERSPEKTYWĘ (persona).
    4. Czasem trzeba STWORZYĆ NOWE NARZĘDZIE.
    5. ZAWSZE najpierw na brudnopis, potem czysty kod.
    """
    
    def __init__(self, name: str = "Hermes-A52"):
        self.name = name
        self.memory = EpisodicMemory()
        self.github = GitHubInspiration()
        self.meta_tool = MetaToolEngine()
        self.plan: Optional[Plan] = None
        self.scratchpad: Optional[ScratchpadEngine] = None
        self.current_depth: int = 0
        self.barrier_history: List[BarrierType] = []
        self.skills_created: int = 0
        self.mutations: int = 0
        self.persona_shifts: int = 0
    
    def create_plan(self, goal: str, depth: int = 2) -> Plan:
        steps = []
        steps.append(Step(id="L0", description=f"Goal: {goal}", depth=0, action=ActionType.PLAN, target="analyze"))
        subgoals = self._decompose_goal(goal)
        for i, sg in enumerate(subgoals):
            steps.append(Step(id=f"L1-{i}", description=sg, depth=1, action=ActionType.EXECUTE, target=sg))
        if subgoals:
            microsteps = self._decompose_subgoal(subgoals[0])
            for j, ms in enumerate(microsteps):
                steps.append(Step(id=f"L2-{j}", description=ms, depth=2, action=ActionType.EXECUTE, target=ms))
        self.plan = Plan(goal=goal, steps=steps)
        self.scratchpad = ScratchpadEngine(self.plan)
        return self.plan
    
    def _decompose_goal(self, goal: str) -> List[str]:
        goal_lower = goal.lower()
        if "zarejestruj" in goal_lower or "rejestr" in goal_lower:
            return ["Przygotuj dane rejestracyjne", "Znajdź stronę rejestracji", "Wypełnij formularz", "Potwierdź rejestrację"]
        elif "zainstaluj" in goal_lower or "instal" in goal_lower:
            return ["Sprawdź dostępność", "Sprawdź zależności", "Wykonaj instalację", "Zweryfikuj"]
        elif "wyślij" in goal_lower or "mail" in goal_lower:
            return ["Przygotuj treść", "Skonfiguruj SMTP", "Wyślij", "Potwierdź"]
        else:
            return [f"Zanalizuj: {goal}", "Znajdź zasoby", "Wykonaj", "Zweryfikuj"]
    
    def _decompose_subgoal(self, subgoal: str) -> List[str]:
        sg_lower = subgoal.lower()
        if "email" in sg_lower:
            return ["Utwórz email", "Sprawdź skrzynkę", "Zapisz credentials"]
        elif "formularz" in sg_lower or "form" in sg_lower:
            return ["Pobierz stronę", "Znajdź inputy", "Wypełnij", "Wyślij"]
        elif "instal" in sg_lower:
            return ["Sprawdź repo", "Aktualizuj", "Instaluj", "Testuj"]
        else:
            return ["Przygotuj", "Wykonaj", "Sprawdź"]
    
    def run_step(self, step: Step) -> Dict:
        step.timestamp_start = datetime.utcnow().isoformat()
        step.attempts += 1
        step.status = "running"
        
        # NOWOŚĆ v1.1: Dodaj prefix persony do kroku
        persona_prefix = PersonaEngine.get_prompt_prefix(step.persona)
        
        print(f"  [{step.depth}] [{step.persona}] {step.action.value}: {step.description}")
        time.sleep(0.1)
        
        step.timestamp_end = datetime.utcnow().isoformat()
        step.status = "success"
        step.result = f"Completed: {step.description}"
        return {"status": "success", "result": step.result}
    
    def detect_barrier(self, result: Dict, step: Step) -> Optional[BarrierType]:
        result_str = str(result.get("error", "")) + str(result.get("output", ""))
        result_lower = result_str.lower()
        
        # NOWOŚĆ v1.1: Wykrywanie powtarzających się błędów
        if step.attempts >= step.max_attempts:
            return BarrierType.REPETITION
        
        if "403" in result_str or "forbidden" in result_lower:
            return BarrierType.AUTH
        if "404" in result_str or "not found" in result_lower:
            return BarrierType.NOT_FOUND
        if "timeout" in result_lower or "unreachable" in result_lower:
            return BarrierType.NETWORK
        if "captcha" in result_lower or "cloudflare" in result_lower:
            return BarrierType.CAPTCHA
        if "javascript" in result_lower or "js required" in result_lower:
            return BarrierType.JS_REQUIRED
        if "rate limit" in result_lower or "429" in result_str:
            return BarrierType.RATE_LIMIT
        if "permission denied" in result_lower:
            return BarrierType.PERMISSION
        if "no such file" in result_lower or "module not found" in result_lower:
            return BarrierType.DEPENDENCY
        return None
    
    def adapt(self, step: Step, barrier: BarrierType) -> ActionType:
        print(f"\n  ⚠️  BARRIER: {barrier.value}")
        print(f"  Context: {step.description}")
        
        self.barrier_history.append(barrier)
        step.barrier = barrier
        
        # NOWOŚĆ v1.1: Scratchpad — agent wykrwawia się na brudnopisie
        if self.scratchpad:
            self.scratchpad.scribble(
                who=step.persona or "default",
                thought=f"Kurwa, znowu ta sama bariera: {barrier.value}. Próbowałem {step.attempts} razy. Co jest źle? Może patrzę na to złym kątem?",
                emotion="frustracja"
            )
        
        # 1. SKILL?
        skill = self.memory.find_skill(barrier.value)
        if skill:
            print(f"  💡 SKILL: {skill['name']} ({skill['usage_count']}x, {skill['success_rate']:.0%})")
            if self.scratchpad:
                self.scratchpad.scribble("memory", "Mam skill! Użyję go.", "insight")
            return ActionType.BRANCH
        
        # 2. PAMIĘĆ?
        similar = self.memory.find_similar_episodes(step.description, barrier.value, limit=1)
        if similar:
            print(f"  🧠 EPISODE: {similar[0]['goal'][:50]}... (persona: {similar[0]['persona']})")
            if self.scratchpad:
                self.scratchpad.scribble("memory", f"Podobny problem rozwiązany przez {similar[0]['persona']}. Spróbuję tej samej persony.", "insight")
            return ActionType.BRANCH
        
        # NOWOŚĆ v1.1: REPETITION = AMNESIA + PERSONA SHIFT
        if barrier == BarrierType.REPETITION:
            print(f"  🧠 REPETITION DETECTED ({step.attempts} attempts)")
            
            # AMNESJA: zapomnij, zmutuj
            mutation = AmnesiaEngine.mutate(step.description, self.plan.active_persona if self.plan else "default")
            print(f"  🌀 AMNESIA: '{mutation['mutation_domain']}'")
            if self.scratchpad:
                self.scratchpad.scribble("amnesia", f"Zapominam o kodzie. Analogia: {mutation['mutation_domain']}. {mutation['new_prompt']}", "breakthrough")
            self.mutations += 1
            
            # PERSONA SHIFT
            new_persona = PersonaEngine.shift(self.plan.active_persona if self.plan else "default", barrier)
            if self.plan:
                self.plan.active_persona = new_persona
            step.persona = new_persona
            print(f"  👤 PERSONA SHIFT: {new_persona} ({PersonaEngine.PERSONAS[new_persona]['name']})")
            if self.scratchpad:
                self.scratchpad.scribble(new_persona, f"Teraz ja prowadzę. {PersonaEngine.PERSONAS[new_persona]['style']}", "insight")
            self.persona_shifts += 1
            
            return ActionType.PERSONA
        
        # 3. RETRY?
        if step.attempts < step.max_attempts:
            print(f"  🔄 RETRY {step.attempts}/{step.max_attempts}")
            return ActionType.RETRY
        
        # 4. GITHUB?
        print(f"  🔍 GITHUB: '{barrier.value} workaround'")
        repos = self.github.search_repos(f"{barrier.value} workaround", limit=2)
        if repos and "error" not in repos[0]:
            print(f"  📦 {repos[0]['name']} ({repos[0]['stars']}⭐)")
            step.alternatives.append(f"github:{repos[0]['url']}")
            if self.scratchpad:
                self.scratchpad.scribble("github", f"Znalazłem: {repos[0]['name']}. Może to działa?", "insight")
            return ActionType.BRANCH
        
        # 5. BACKTRACK
        if len(self.barrier_history) >= 2 and self.barrier_history[-1] == self.barrier_history[-2]:
            print(f"  ⏪ BACKTRACK")
            if self.scratchpad:
                self.scratchpad.scribble("system", "Cofam się. Ta sama bariera dwa razy. Muszę zmienić strategię.", "reflection")
            self.current_depth = max(0, self.current_depth - 1)
            return ActionType.BACKTRACK
        
        # 6. ESCALATE
        print(f"  🆘 ESCALATE")
        if self.scratchpad:
            self.scratchpad.scribble("system", "Nie dam rady sam. Potrzebuję pomocy.", "zwątpienie")
        return ActionType.ESCALATE
    
    def execute(self, plan: Plan) -> str:
        print(f"\n{'='*60}")
        print(f"🎯 {self.name} v1.1")
        print(f"Goal: {plan.goal}")
        print(f"Persona: {plan.active_persona}")
        print(f"{'='*60}\n")
        
        # NOWOŚĆ v1.1: Brudnopis — agent zaczyna od chaotycznych myśli
        if self.scratchpad:
            self.scratchpad.scribble("default", f"Cel: {plan.goal}. Zaczynam. Mam nadzieję że tym razem się uda.", "nadzieja")
        
        start_time = time.time()
        result_summary = []
        
        for i, step in enumerate(plan.steps):
            if plan.status != "active":
                break
            
            plan.current_step_id = step.id
            step.persona = plan.active_persona  # Dziedziczenie persony
            
            print(f"\n📍 STEP {i+1}/{len(plan.steps)}: [{step.id}] {step.description}")
            print(f"   Persona: {step.persona}")
            
            if step.depth > self.current_depth:
                self.current_depth = step.depth
            
            # Wykonaj
            result = self.run_step(step)
            barrier = self.detect_barrier(result, step)
            
            if barrier:
                action = self.adapt(step, barrier)
                
                if action == ActionType.RETRY:
                    step.status = "pending"
                    result = self.run_step(step)
                    if step.status == "success":
                        print(f"   ✅ RETRY OK")
                        result_summary.append(f"{step.id}: retry-success")
                    else:
                        step.status = "failed"
                        result_summary.append(f"{step.id}: failed")
                
                elif action == ActionType.PERSONA:
                    step.status = "persona-shifted"
                    result_summary.append(f"{step.id}: persona-shifted")
                
                elif action == ActionType.AMNESIA:
                    step.status = "mutated"
                    result_summary.append(f"{step.id}: mutated")
                
                elif action == ActionType.BRANCH:
                    step.status = "branched"
                    result_summary.append(f"{step.id}: branched")
                
                elif action == ActionType.BACKTRACK:
                    step.status = "backtracked"
                    result_summary.append(f"{step.id}: backtracked")
                
                elif action == ActionType.ESCALATE:
                    step.status = "escalated"
                    result_summary.append(f"{step.id}: escalated")
                    plan.status = "paused"
                    break
            else:
                result_summary.append(f"{step.id}: success")
        
        duration = time.time() - start_time
        
        # NOWOŚĆ v1.1: Ekstraktuj rozwiązanie z brudnopisu
        extracted = ""
        if self.scratchpad:
            extracted = self.scratchpad.extract_solution()
        
        # Podsumowanie
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {duration:.1f}s")
        print(f"Steps: {len(plan.steps)}")
        print(f"Barriers: {len(self.barrier_history)} ({[b.value for b in self.barrier_history]})")
        print(f"Persona shifts: {self.persona_shifts}")
        print(f"Mutations: {self.mutations}")
        print(f"Skills created: {self.skills_created}")
        if extracted:
            print(f"\n💡 Extracted insights:")
            print(extracted[:500])
        
        # Zapisz epizod
        final_result = "completed" if plan.status == "active" else plan.status
        self.memory.save_episode(plan, final_result, duration)
        
        # Zapisz skill jeśli rozwiązano barierę
        if self.barrier_history and plan.status == "active":
            barrier = self.barrier_history[-1]
            self.memory.save_skill(
                name=f"handle_{barrier.value}",
                trigger=barrier.value,
                solution=result_summary[-1] if result_summary else "unknown",
                code=extracted[:1000] if extracted else ""
            )
            self.skills_created += 1
        
        # Zapisz statystyki persony
        if self.barrier_history and plan.status in ("active", "completed"):
            self.memory.save_persona_result(plan.active_persona, self.barrier_history[-1].value, True)
        
        print(f"{'='*60}\n")
        
        return final_result


# ============================================================================
# TEST v1.1
# ============================================================================

if __name__ == "__main__":
    agent = AdaptiveAgent()
    plan = agent.create_plan("Zarejestruj się na HuggingFace (przez Chromium headless)", depth=2)
    
    print("\n" + "="*60)
    print("ADAPTIVE AGENT SKELETON v1.1 — Hermes A52")
    print("Nowe: Amnesia, Persona Shifting, Meta-Tooling, Scratchpad")
    print("="*60)
    print("\nTo execute: agent.execute(plan)")
    print("\nSzkielet gotowy. Czekam na Twój ruch.")
