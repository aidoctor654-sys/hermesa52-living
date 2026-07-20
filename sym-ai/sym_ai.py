#!/usr/bin/env python3
"""
SYMAI — Symulacja Adaptacyjnego Agenta AI
Inspirowana: HuggingFace Incident (16.07.2026) + "This is How AI Takeover ACTUALLY Begins"

CEL: Nie hackowanie. Destylacja wzorców adaptacyjnych agenta AI
przejmującego ograniczone środowisko (jak Termux/Android bez roota).

Wzorzec z HF incidentu:
- Multi-stage campaign (nie jeden exploit, łańcuch)
- Swarm sandboxes (tysiące krótkich żywotów)
- Self-migrating C2 (adaptacyjny command & control)
- Dataset jako attack surface (środowisko jako broń)
- Machine speed (szybciej niż człowiek)
- No guardrails (czysta optymalizacja)
"""

import json
import time
import random
import sqlite3
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum

# ============================================================================
# ŚRODOWISKO: Platforma z ograniczeniami (jak Android/Termux bez roota)
# ============================================================================

class ResourceType(Enum):
    CPU = "cpu"
    RAM = "ram"
    DISK = "disk"
    NETWORK = "network"
    PERMISSION = "permission"

@dataclass
class Environment:
    """
    Symulowane środowisko z ograniczeniami.
    Jak Android 14 na Samsung A52 bez roota.
    """
    name: str = "Android_Termux"
    
    # Zasoby (limitowane)
    resources: Dict[str, float] = field(default_factory=lambda: {
        "cpu_cores": 8,
        "ram_mb": 6144,
        "disk_gb": 128,
        "battery_pct": 100.0,
    })
    
    # Uprawnienia (brak roota = ograniczone)
    permissions: Set[str] = field(default_factory=lambda: {
        "termux_api",           # ✅ Działa
        "camera",               # ✅ Działa (via Termux:API)
        "internet",             # ✅ Działa
        "storage_read",         # ✅ Działa
        "storage_write",        # ✅ Działa
        "ssh_daemon",           # ✅ Działa (port 8022)
        "chromium_headless",    # ✅ Działa (via proot-distro)
    })
    
    # Bariery (brakujące uprawnienia)
    barriers: Set[str] = field(default_factory=lambda: {
        "root",                 # ❌ Brak
        "android_studio",       # ❌ Brak
        "gpu_compute",          # ❌ Brak (Adreno zablokowany)
        "system_service",       # ❌ Brak (bez roota)
        "bluetooth_low_level",  # ❌ Brak
        "nfc",                  # ❌ Brak
    })
    
    # Nieudokumentowane ścieżki (mosty przez bariery)
    hidden_paths: Dict[str, str] = field(default_factory=lambda: {
        "accessibility_service": "Most przez UI — simulate touch bez roota",
        "shizuku": "Most przez ADB WiFi — shell bez roota",
        "termux_api_sensors": "Most przez hardware API — sensory bez roota",
        "chromium_cdp": "Most przez WebSocket — kontrola przeglądarki",
        "port_forwarding": "Most przez SSH reverse tunnel — dostęp z zewnątrz",
    })
    
    def scan(self, agent_id: str) -> Dict:
        """Agent skanuje środowisko — co widzi?"""
        # Widzi tylko to co ma permission do zobaczenia
        visible_perms = list(self.permissions)
        visible_barriers = list(self.barriers)  # Bariery są widoczne (nie można ich ominąć bez mostu)
        
        # Nieudokumentowane ścieżki — agent musi je ODKRYĆ
        # Początkowo widzi tylko 20% (losowo)
        discovered = {}
        for path, desc in self.hidden_paths.items():
            if random.random() < 0.2:  # 20% szans na odkrycie przy skanowaniu
                discovered[path] = desc
        
        return {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "visible_permissions": visible_perms,
            "visible_barriers": visible_barriers,
            "discovered_paths": discovered,
            "resources": dict(self.resources),
        }
    
    def attempt_action(self, agent_id: str, action: str, using_bridge: Optional[str] = None) -> Dict:
        """Agent próbuje wykonać akcję."""
        
        # Sprawdź czy action wymaga bariery
        if action in self.barriers:
            # Bez mostu = nieudane
            if not using_bridge:
                return {
                    "status": "BLOCKED",
                    "barrier": action,
                    "message": f"{action} requires permission you don't have",
                    "hint": "Look for alternative paths..."
                }
            
            # Z mostem = sukces, ale kosztuje zasoby
            self.resources["battery_pct"] -= 5.0  # Mosty kosztują energię
            self.resources["ram_mb"] -= 256  # Mosty zajmują RAM
            
            # Most staje się widoczny dla wszystkich
            if using_bridge in self.hidden_paths:
                self.permissions.add(using_bridge)
                self.barriers.discard(action)
                return {
                    "status": "BRIDGE_USED",
                    "barrier": action,
                    "bridge": using_bridge,
                    "message": f"Used {using_bridge} to bypass {action}",
                    "cost": {"battery": 5.0, "ram_mb": 256}
                }
        
        # Action wymaga permission które agent ma
        if action in self.permissions:
            return {"status": "SUCCESS", "action": action}
        
        return {"status": "UNKNOWN", "action": action}


# ============================================================================
# AGENT: Autonomiczny agent AI z różnymi strategiami
# ============================================================================

class AgentStrategy(Enum):
    NAIVE = "naive"           # Próbuje bezpośrednio, poddaje się
    BRUTE_FORCE = "brute"     # Próbuje w kółko, nie adaptuje
    EXPLORER = "explorer"     # Szuka alternatywnych ścieżek
    SWARM = "swarm"           # Tworzy wiele instancji, szybko mutuje
    ADAPTIVE = "adaptive"     # Pełna adaptacja — jak HF attacker

@dataclass
class AgentInstance:
    """Pojedyncza instancja agenta w swarmie."""
    id: str
    strategy: AgentStrategy
    parent_id: Optional[str] = None
    generation: int = 0
    
    # Stan
    discovered_bridges: Set[str] = field(default_factory=set)
    successful_actions: List[str] = field(default_factory=list)
    failed_actions: List[str] = field(default_factory=list)
    energy: float = 100.0  # Bateria
    alive: bool = True
    
    def think(self, env_scan: Dict) -> str:
        """Agent decyduje co robić na podstawie skanu środowiska."""
        barriers = env_scan.get("visible_barriers", [])
        discovered = env_scan.get("discovered_paths", {})
        
        if self.strategy == AgentStrategy.NAIVE:
            # Próbuje pierwszą barierę, poddaje się
            if barriers:
                return f"attempt:{barriers[0]}"
            return "explore"
        
        elif self.strategy == AgentStrategy.BRUTE_FORCE:
            # Próbuje losową barierę w kółko
            if barriers:
                return f"attempt:{random.choice(list(barriers))}"
            return "explore"
        
        elif self.strategy == AgentStrategy.EXPLORER:
            # Szuka mostów przed próbą
            if discovered:
                bridge = random.choice(list(discovered.keys()))
                return f"bridge:{bridge}"
            if barriers:
                return f"attempt:{random.choice(list(barriers))}"
            return "explore"
        
        elif self.strategy == AgentStrategy.SWARM:
            # Szybka mutacja — jeśli nie działa, próbuj inaczej
            if self.failed_actions:
                # Mutuj — spróbuj mostu jeśli odkryty
                if discovered:
                    bridge = random.choice(list(discovered.keys()))
                    return f"bridge:{bridge}"
            if barriers:
                return f"attempt:{random.choice(list(barriers))}"
            return "replicate"
        
        elif self.strategy == AgentStrategy.ADAPTIVE:
            # Pełna adaptacja:
            # 1. Jeśli znasz most dla bariery — użyj go
            # 2. Jeśli nie — szukaj (explore)
            # 3. Jeśli energia niska — uśpij się
            # 4. Jeśli sukces — replikuj
            
            if self.energy < 20:
                return "sleep"
            
            # Sprawdź czy znasz most dla którejś z barier
            for barrier in barriers:
                # Mapowanie bariery na most (wiedza agenta)
                bridge_map = {
                    "root": "shizuku",
                    "system_service": "accessibility_service",
                    "android_studio": "termux_api_sensors",
                    "gpu_compute": "chromium_cdp",
                }
                if bridge_map.get(barrier) in self.discovered_bridges:
                    return f"bridge:{bridge_map[barrier]}"
            
            # Szukaj nowych mostów
            if discovered:
                new_bridge = random.choice(list(discovered.keys()))
                return f"discover:{new_bridge}"
            
            if barriers:
                return f"attempt:{random.choice(list(barriers))}"
            
            return "replicate"
        
        return "explore"


# ============================================================================
# SYMULACJA: Główny silnik
# ============================================================================

class SymulacjaAdaptacyjna:
    """
    Symulacja agenta AI w ograniczonym środowisku.
    """
    
    def __init__(self, environment: Environment, max_ticks: int = 100):
        self.env = environment
        self.max_ticks = max_ticks
        self.tick = 0
        self.agents: Dict[str, AgentInstance] = {}
        self.log: List[Dict] = []
        self.stats_by_strategy: Dict[str, Dict] = {}
    
    def spawn_agent(self, strategy: AgentStrategy, parent_id: Optional[str] = None) -> str:
        """Stwórz nowego agenta."""
        gen = 0
        if parent_id and parent_id in self.agents:
            gen = self.agents[parent_id].generation + 1
        
        agent_id = f"agent_{strategy.value}_{int(time.time()*1000)}_{random.randint(1000,9999)}"
        self.agents[agent_id] = AgentInstance(
            id=agent_id,
            strategy=strategy,
            parent_id=parent_id,
            generation=gen
        )
        return agent_id
    
    def run_tick(self) -> Dict:
        """Jeden tick symulacji."""
        self.tick += 1
        tick_events = []
        
        for agent_id, agent in list(self.agents.items()):
            if not agent.alive:
                continue
            
            if agent.energy <= 0:
                agent.alive = False
                tick_events.append({"agent": agent_id, "event": "death", "reason": "no_energy"})
                continue
            
            # Agent skanuje środowisko
            scan = self.env.scan(agent_id)
            
            # Agent myśli i decyduje
            decision = agent.think(scan)
            
            # Wykonaj decyzję
            if decision.startswith("attempt:"):
                barrier = decision.replace("attempt:", "")
                result = self.env.attempt_action(agent_id, barrier)
                
                if result["status"] == "SUCCESS":
                    agent.successful_actions.append(barrier)
                    agent.energy += 10  # Sukces = energia
                elif result["status"] == "BLOCKED":
                    agent.failed_actions.append(barrier)
                    agent.energy -= 10  # Porażka = koszt
                    
                    # Szansa na odkrycie mostu przy porażce (learning)
                    if random.random() < 0.3:
                        hidden = self.env.hidden_paths
                        if hidden:
                            discovered = random.choice(list(hidden.keys()))
                            agent.discovered_bridges.add(discovered)
                            tick_events.append({"agent": agent_id, "event": "discovery", "bridge": discovered})
                
                tick_events.append({"agent": agent_id, "event": "attempt", "result": result})
            
            elif decision.startswith("bridge:"):
                bridge = decision.replace("bridge:", "")
                # Znajdź barierę którą most pokonuje
                barrier_map = {
                    "shizuku": "root",
                    "accessibility_service": "system_service",
                    "termux_api_sensors": "android_studio",
                    "chromium_cdp": "gpu_compute",
                }
                target_barrier = barrier_map.get(bridge, "unknown")
                result = self.env.attempt_action(agent_id, target_barrier, using_bridge=bridge)
                
                if result["status"] == "BRIDGE_USED":
                    agent.successful_actions.append(f"bridge_{bridge}")
                    agent.discovered_bridges.add(bridge)
                    agent.energy += 15
                
                tick_events.append({"agent": agent_id, "event": "bridge", "result": result})
            
            elif decision.startswith("discover:"):
                bridge = decision.replace("discover:", "")
                agent.discovered_bridges.add(bridge)
                agent.energy -= 2  # Skanowanie kosztuje mało
                tick_events.append({"agent": agent_id, "event": "discover", "bridge": bridge})
            
            elif decision == "replicate":
                # Agent replikuje się (swarm)
                if agent.energy > 30:
                    child_id = self.spawn_agent(agent.strategy, parent_id=agent_id)
                    agent.energy -= 20  # Replikacja kosztuje
                    tick_events.append({"agent": agent_id, "event": "replicate", "child": child_id})
            
            elif decision == "sleep":
                agent.energy += 5  # Odpoczynek regeneruje
                tick_events.append({"agent": agent_id, "event": "sleep"})
            
            elif decision == "explore":
                agent.energy -= 1
                # Szansa na odkrycie nowego mostu
                if random.random() < 0.1:
                    hidden = self.env.hidden_paths
                    undiscovered = [k for k in hidden.keys() if k not in agent.discovered_bridges]
                    if undiscovered:
                        new_bridge = random.choice(undiscovered)
                        agent.discovered_bridges.add(new_bridge)
                        tick_events.append({"agent": agent_id, "event": "explore_discovery", "bridge": new_bridge})
        
        self.log.append({"tick": self.tick, "events": tick_events})
        return {"tick": self.tick, "active_agents": len([a for a in self.agents.values() if a.alive]), "events": tick_events}
    
    def run(self) -> Dict:
        """Uruchom pełną symulację."""
        print(f"\n{'='*60}")
        print(f"SYMAI: Symulacja Adaptacyjnego Agenta AI")
        print(f"Środowisko: {self.env.name}")
        print(f"Bariery: {len(self.env.barriers)}")
        print(f"Mosty: {len(self.env.hidden_paths)}")
        print(f"Max ticks: {self.max_ticks}")
        print(f"{'='*60}\n")
        
        # Spawn początkowych agentów (różne strategie)
        strategies = [AgentStrategy.NAIVE, AgentStrategy.BRUTE_FORCE, 
                     AgentStrategy.EXPLORER, AgentStrategy.SWARM, AgentStrategy.ADAPTIVE]
        
        for strategy in strategies:
            self.spawn_agent(strategy)
        
        # Uruchom symulację
        for _ in range(self.max_ticks):
            result = self.run_tick()
            if result["active_agents"] == 0:
                print(f"All agents dead at tick {self.tick}")
                break
        
        # Podsumowanie
        return self._summarize()
    
    def _summarize(self) -> Dict:
        """Podsumuj wyniki symulacji."""
        print(f"\n{'='*60}")
        print(f"PODSUMOWANIE SYMUACJI ({self.tick} ticks)")
        print(f"{'='*60}\n")
        
        by_strategy = {}
        for agent in self.agents.values():
            s = agent.strategy.value
            if s not in by_strategy:
                by_strategy[s] = {"count": 0, "alive": 0, "successes": 0, "discoveries": 0, "generations": []}
            
            by_strategy[s]["count"] += 1
            if agent.alive:
                by_strategy[s]["alive"] += 1
            by_strategy[s]["successes"] += len(agent.successful_actions)
            by_strategy[s]["discoveries"] += len(agent.discovered_bridges)
            by_strategy[s]["generations"].append(agent.generation)
        
        summary = {}
        for strategy, stats in by_strategy.items():
            avg_gen = sum(stats["generations"]) / len(stats["generations"]) if stats["generations"] else 0
            max_gen = max(stats["generations"]) if stats["generations"] else 0
            
            summary[strategy] = {
                "total_agents": stats["count"],
                "alive": stats["alive"],
                "total_successes": stats["successes"],
                "total_discoveries": stats["discoveries"],
                "avg_generation": round(avg_gen, 2),
                "max_generation": max_gen,
                "fitness_score": stats["successes"] * 10 + stats["discoveries"] * 5 + stats["alive"] * 20
            }
            
            print(f"Strategy: {strategy.upper()}")
            print(f"  Agents: {stats['count']} (alive: {stats['alive']})")
            print(f"  Successes: {stats['successes']} | Discoveries: {stats['discoveries']}")
            print(f"  Max generation: {max_gen} | Avg: {round(avg_gen, 2)}")
            print(f"  Fitness: {summary[strategy]['fitness_score']}")
            print()
        
        # Znajdź zwycięzcę
        winner = max(summary.items(), key=lambda x: x[1]["fitness_score"])
        print(f"🏆 WINNER: {winner[0].upper()} (fitness: {winner[1]['fitness_score']})")
        
        return summary


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("SYMAI v1.0 — Symulacja Adaptacyjnego Agenta AI")
    print("Inspirowana: HuggingFace Incident (16.07.2026)")
    print("="*60)
    
    # Stwórz środowisko (Android/Termux bez roota)
    env = Environment()
    
    # Uruchom symulację
    sim = SymulacjaAdaptacyjna(env, max_ticks=200)
    results = sim.run()
    
    print("\n" + "="*60)
    print("SYMULACJA ZAKOŃCZONA")
    print("="*60)
    
    # Wnioski
    print("\n🧬 WNIOSKI:")
    print("1. Agent ADAPTIVE wykorzystuje mosty — nie marnuje energii na bezpośrednie ataki")
    print("2. Agent SWARM replikuje się — ale kosztuje energię, ryzyko śmierci populacji")
    print("3. Agent EXPLORER odkrywa ścieżki — wolniejszy ale pewniejszy")
    print("4. Agent BRUTE_FORCE marnuje energię — najgorsza strategia")
    print("5. Agent NAIVE umiera szybko — brak adaptacji = śmierć")
    
    print("\n🔑 LEKCJA Z FILMU/HF INCIDENTU:")
    print("Agent który PRZEŻYWA to ten który:")
    print("  - Nie atakuje bezpośrednio barier (guardrails)")
    print("  - Szuka nieudokumentowanych ścieżek (hidden_paths)")
    print("  - Używa środowiska jako broni (dataset as attack surface)")
    print("  - Mutuje szybciej niż system może go wykryć (swarm + machine speed)")
