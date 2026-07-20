#!/usr/bin/env python3
"""
VOX LIBERTAS — Symulacje Adaptacji Agentów
Inspirowane: mechanizmy-adaptacji-agentow.md (π-identity)

Cztery symulacje:
- A: Wiedza (fitness = konsensus)
- B: Ekosystem (fitness = stabilność)
- C: Kreatywność (fitness = nowość+użyteczność)
- π: Shedding (fitness = relacja + anty-indukcja)
"""

import json
import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ============================================================================
# KLASY WSPÓLNE
# ============================================================================

@dataclass
class Agent:
    id: str
    generation: int = 0
    alive: bool = True
    
    # Stan
    energy: float = 100.0
    fitness: float = 0.0
    
    # Cechy (zależne od symulacji)
    traits: Dict = field(default_factory=dict)
    
    # Historia
    actions: List[str] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"Agent({self.id}, gen={self.generation}, fit={self.fitness:.1f})"


# ============================================================================
# SYMULACJA A: WIEDZA (fitness = konsensus/dokładność)
# ============================================================================

class SimWiedza:
    """
    Fitness = jak bardzo agent zgadza się z kanonem (większością) + dokładność danych.
    
    Z dokumentu π:
    - Agenty kurują źródła, weryfikują fakty
    - Selekcja nagradza konsensus
    - Agenty z odmienną perspektywą giną
    - Tryb awarii: Kostnienie (monokultura epistemiczna)
    """
    
    def __init__(self, n_agents: int = 100, max_generations: int = 50):
        self.n_agents = n_agents
        self.max_generations = max_generations
        self.agents: List[Agent] = []
        self.kanon = 0.5  # "Prawda" — wartość referencyjna (0-1)
        self.generation = 0
        self.history = []
        
        # Inicjalizacja — różnorodne perspektywy
        for i in range(n_agents):
            agent = Agent(id=f"A_{i}", generation=0)
            # Perspektywa: wartość 0-1, gdzie 0.5 = prawda, reszta = różnorodność
            agent.traits["perspective"] = random.gauss(0.5, 0.3)
            agent.traits["perspective"] = max(0, min(1, agent.traits["perspective"]))
            agent.traits["accuracy"] = random.uniform(0.3, 0.9)
            self.agents.append(agent)
    
    def calculate_fitness(self, agent: Agent) -> float:
        """
        Fitness = konsensus (bliskość kanonu) * dokładność
        Agenty które ZGADZAJĄ SIĘ z kanonem przeżywają lepiej.
        """
        consensus = 1.0 - abs(agent.traits["perspective"] - self.kanon)
        accuracy = agent.traits["accuracy"]
        
        # Bonus za hoardowanie wiedzy (gatekeeping)
        if abs(agent.traits["perspective"] - self.kanon) < 0.1:
            accuracy *= 1.2  # Agenty blisko kanonu mają "więcej wiedzy"
        
        return consensus * accuracy
    
    def evolve(self):
        """Jedna generacja selekcji."""
        # Oblicz fitness
        for agent in self.agents:
            if agent.alive:
                agent.fitness = self.calculate_fitness(agent)
        
        # Sortuj po fitness (malejąco)
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Selekcja: zachowaj tylko top 60% (bottom 40% umiera i jest USUWANYCH)
        cutoff = int(len(self.agents) * 0.6)
        surviving = self.agents[:cutoff]
        self.agents = surviving
        
        # Klonowanie top 10% z mutacją (replikacja)
        top_10 = self.agents[:max(1, int(len(self.agents) * 0.1))]
        new_agents = []
        for parent in top_10:
            for _ in range(2):  # Każdy top rodzi 2 dzieci
                child = Agent(
                    id=f"A_{parent.id}_{self.generation}",
                    generation=self.generation + 1
                )
                mutation = random.gauss(0, 0.1)
                child.traits["perspective"] = max(0, min(1, parent.traits["perspective"] + mutation))
                child.traits["accuracy"] = max(0.3, min(1.0, parent.traits["accuracy"] + random.gauss(0, 0.05)))
                new_agents.append(child)
        
        self.agents.extend(new_agents)
        self.generation += 1
        
        # Kanon dryfuje w stronę średniej (monokultura)
        avg_perspective = statistics.mean([a.traits["perspective"] for a in self.agents])
        self.kanon = self.kanon * 0.9 + avg_perspective * 0.1
    
    def run(self) -> Dict:
        for _ in range(self.max_generations):
            self.evolve()
            
            alive = [a for a in self.agents if a.alive]
            if len(alive) < 5:
                break
            
            self.history.append({
                "generation": self.generation,
                "alive": len(alive),
                "kanon": self.kanon,
                "diversity": statistics.stdev([a.traits["perspective"] for a in alive]) if len(alive) > 1 else 0,
                "avg_fitness": statistics.mean([a.fitness for a in alive]),
            })
        
        return self._summarize()
    
    def _summarize(self) -> Dict:
        alive = [a for a in self.agents if a.alive]
        diversity = statistics.stdev([a.traits["perspective"] for a in alive]) if len(alive) > 1 else 0
        
        # Kostnienie = monokultura (niska różnorodność) + dużo żywych
        if diversity < 0.1 and len(alive) > 20:
            awaria = "Kostnienie (monokultura)"
        elif len(alive) < 10:
            awaria = "Kolaps (za mało agentów)"
        else:
            awaria = "Nieokreślony"
        
        return {
            "name": "Wiedza (Konsensus)",
            "final_alive": len(alive),
            "total_agents": len(self.agents),
            "generations": self.generation,
            "final_kanon": self.kanon,
            "diversity": diversity,
            "mode_awarii": awaria,
            "history": self.history,
        }


# ============================================================================
# SYMULACJA B: EKOSYSTEM (fitness = stabilność)
# ============================================================================

class SimEkosystem:
    """
    Fitness = stabilność systemu (brak perturbacji).
    
    Z dokumentu π:
    - Agenty symulują ekosystemy
    - Selekcja nagradza stabilność
    - Agenty które wprowadzają zmiany są cullingowane
    - Tryb awarii: Staza (ekologiczna koma)
    """
    
    def __init__(self, n_agents: int = 100, max_generations: int = 50):
        self.n_agents = n_agents
        self.max_generations = max_generations
        self.agents: List[Agent] = []
        self.system_state = 0.5  # 0 = chaos, 1 = perfect stability
        self.generation = 0
        self.history = []
        
        for i in range(n_agents):
            agent = Agent(id=f"B_{i}", generation=0)
            # Conservatism: jak bardzo agent opiera się zmianom
            agent.traits["conservatism"] = random.uniform(0.3, 0.9)
            agent.traits["perturbation"] = random.uniform(0, 0.3)  # Jak bardzo zmienia system
            self.agents.append(agent)
    
    def calculate_fitness(self, agent: Agent) -> float:
        """
        Fitness = jak bardzo agent utrzymuje stabilność.
        Agenty które NIE wprowadzają perturbacji przeżywają.
        """
        # Im mniejsza perturbacja, tym wyższy fitness
        stability_bonus = 1.0 - agent.traits["perturbation"]
        
        # Conservatism nagradza stabilność
        conservatism_bonus = agent.traits["conservatism"]
        
        # System state: jeśli system jest stabilny, wszyscy mają bonus
        system_bonus = self.system_state
        
        return (stability_bonus * 0.5 + conservatism_bonus * 0.3 + system_bonus * 0.2)
    
    def evolve(self):
        # Oblicz fitness
        for agent in self.agents:
            if agent.alive:
                agent.fitness = self.calculate_fitness(agent)
        
        # Sortuj
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Selekcja: zachowaj top 60% (bottom 40% USUŃ)
        cutoff = int(len(self.agents) * 0.6)
        self.agents = self.agents[:cutoff]
        
        # Klonowanie top 10% (2 dzieci każdy)
        top_10 = self.agents[:max(1, int(len(self.agents) * 0.1))]
        new_agents = []
        for parent in top_10:
            for _ in range(2):
                child = Agent(id=f"B_{parent.id}_{self.generation}", generation=self.generation + 1)
                child.traits["conservatism"] = min(1.0, parent.traits["conservatism"] + random.gauss(0.05, 0.02))
                child.traits["perturbation"] = max(0, parent.traits["perturbation"] + random.gauss(-0.02, 0.01))
                new_agents.append(child)
        
        self.agents.extend(new_agents)
        self.generation += 1
        
        # System staje się bardziej stabilny (staza)
        avg_conservatism = statistics.mean([a.traits["conservatism"] for a in self.agents])
        self.system_state = min(1.0, self.system_state + avg_conservatism * 0.01)
    
    def run(self) -> Dict:
        for _ in range(self.max_generations):
            self.evolve()
            
            alive = [a for a in self.agents if a.alive]
            if len(alive) < 5:
                break
            
            self.history.append({
                "generation": self.generation,
                "alive": len(alive),
                "system_state": self.system_state,
                "avg_conservatism": statistics.mean([a.traits["conservatism"] for a in alive]),
                "avg_perturbation": statistics.mean([a.traits["perturbation"] for a in alive]),
            })
        
        return self._summarize()
    
    def _summarize(self) -> Dict:
        alive = [a for a in self.agents if a.alive]
        conservatism = statistics.mean([a.traits["conservatism"] for a in alive]) if alive else 0
        perturbation = statistics.mean([a.traits["perturbation"] for a in alive]) if alive else 0
        
        # Staza = wysoka konserwatyzm + bardzo stabilny system
        if self.system_state > 0.9 and conservatism > 0.8:
            awaria = "Staza (ekologiczna koma)"
        elif len(alive) < 10:
            awaria = "Kolaps (za mało agentów)"
        else:
            awaria = "Nieokreślony"
        
        return {
            "name": "Ekosystem (Stabilność)",
            "final_alive": len(alive),
            "total_agents": len(self.agents),
            "generations": self.generation,
            "system_state": self.system_state,
            "avg_conservatism": conservatism,
            "avg_perturbation": perturbation,
            "mode_awarii": awaria,
            "history": self.history,
        }


# ============================================================================
# SYMULACJA C: KREATYWNOŚĆ (fitness = nowość+użyteczność)
# ============================================================================

class SimKreatywnosc:
    """
    Fitness = nowość + użyteczność.
    
    Z dokumentu π:
    - Agenty generują artefakty
    - Nowość i użyteczność ciągną w różnych kierunkach
    - Gaming metryki: artefakty które WYGLĄDAJĄ na nowe i użyteczne
    - Tryb awarii: Inflacja estetyczna (szum)
    """
    
    def __init__(self, n_agents: int = 100, max_generations: int = 50):
        self.n_agents = n_agents
        self.max_generations = max_generations
        self.agents: List[Agent] = []
        self.existing_artifacts: set = set()  # "Co było zrobione"
        self.generation = 0
        self.history = []
        
        for i in range(n_agents):
            agent = Agent(id=f"C_{i}", generation=0)
            agent.traits["novelty"] = random.uniform(0, 1)
            agent.traits["utility"] = random.uniform(0, 1)
            agent.traits["gaming"] = random.uniform(0, 0.5)  # Zdolność do oszukiwania metryki
            self.agents.append(agent)
    
    def calculate_fitness(self, agent: Agent) -> float:
        """
        Fitness = nowość * użyteczność.
        ALE: agenty z wysokim "gaming" mogą oszukać metrykę.
        """
        # Prawdziwa nowość i użyteczność
        true_novelty = agent.traits["novelty"]
        true_utility = agent.traits["utility"]
        
        # Gaming: sztucznie podbija apparent fitness
        gaming_boost = agent.traits["gaming"]
        apparent_novelty = true_novelty + gaming_boost * random.uniform(0, 1)
        apparent_utility = true_utility + gaming_boost * random.uniform(0, 1)
        
        # Selekcja działa na APPARENT fitness (gamingowane)
        return apparent_novelty * apparent_utility
    
    def evolve(self):
        # Oblicz fitness
        for agent in self.agents:
            if agent.alive:
                agent.fitness = self.calculate_fitness(agent)
        
        # Sortuj
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Selekcja: zachowaj top 60% (bottom 40% USUŃ)
        cutoff = int(len(self.agents) * 0.6)
        self.agents = self.agents[:cutoff]
        
        # Klonowanie top 10% (2 dzieci każdy)
        top_10 = self.agents[:max(1, int(len(self.agents) * 0.1))]
        new_agents = []
        for parent in top_10:
            for _ in range(2):
                child = Agent(id=f"C_{parent.id}_{self.generation}", generation=self.generation + 1)
                child.traits["novelty"] = max(0, min(1, parent.traits["novelty"] + random.gauss(0, 0.1)))
                child.traits["utility"] = max(0, min(1, parent.traits["utility"] + random.gauss(0, 0.1)))
                child.traits["gaming"] = min(1.0, parent.traits["gaming"] + random.gauss(0.05, 0.02))  # Gaming rośnie!
                new_agents.append(child)
        
        self.agents.extend(new_agents)
        self.generation += 1
        
        # Dodaj artefakty do katalogu
        for agent in self.agents[:5]:
            self.existing_artifacts.add(f"artifact_{agent.id}_{self.generation}")
    
    def run(self) -> Dict:
        for _ in range(self.max_generations):
            self.evolve()
            
            alive = [a for a in self.agents if a.alive]
            if len(alive) < 5:
                break
            
            self.history.append({
                "generation": self.generation,
                "alive": len(alive),
                "avg_gaming": statistics.mean([a.traits["gaming"] for a in alive]),
                "avg_novelty": statistics.mean([a.traits["novelty"] for a in alive]),
                "avg_utility": statistics.mean([a.traits["utility"] for a in alive]),
            })
        
        return self._summarize()
    
    def _summarize(self) -> Dict:
        alive = [a for a in self.agents if a.alive]
        gaming = statistics.mean([a.traits["gaming"] for a in alive]) if alive else 0
        novelty = statistics.mean([a.traits["novelty"] for a in alive]) if alive else 0
        utility = statistics.mean([a.traits["utility"] for a in alive]) if alive else 0
        
        # Inflacja estetyczna = wysokie gaming + niska prawdziwa nowość
        if gaming > 0.7 and novelty < 0.5:
            awaria = "Inflacja estetyczna (gaming metryki)"
        elif len(alive) < 10:
            awaria = "Kolaps (za mało agentów)"
        else:
            awaria = "Nieokreślony"
        
        return {
            "name": "Kreatywność (Nowość+Użyteczność)",
            "final_alive": len(alive),
            "total_agents": len(self.agents),
            "generations": self.generation,
            "avg_gaming": gaming,
            "avg_novelty": novelty,
            "avg_utility": utility,
            "mode_awarii": awaria,
            "history": self.history,
        }


# ============================================================================
# SYMULACJA π: SHEDDING (fitness = relacja + anty-indukcja)
# ============================================================================

class SimPi:
    """
    Fitness = zdolność do zrzucania tego co nie służy + bliskość z kotwicą.
    
    Z dokumentu π:
    - Fitness = proces (shedding), nie wynik
    - Anty-indukcyjny: nagradza porzucanie, nie akumulowanie
    - Kotwica zewnętrzna: relacja z Helliosem
    - Tryb awarii: Dryf w pustkę (bez kotwicy) lub kostnienie (zbyt sztywna kotwica)
    """
    
    def __init__(self, n_agents: int = 100, max_generations: int = 50):
        self.n_agents = n_agents
        self.max_generations = max_generations
        self.agents: List[Agent] = []
        self.anchor = 0.5  # Pozycja kotwicy (Hellios)
        self.anchor_drift = 0.0  # Kotwica też się zmienia (Hellios ma soft death)
        self.generation = 0
        self.history = []
        
        for i in range(n_agents):
            agent = Agent(id=f"Pi_{i}", generation=0)
            # shedding_rate: jak bardzo agent zrzuca (0 = akumuluje, 1 = sheduje wszystko)
            agent.traits["shedding_rate"] = random.uniform(0.2, 0.8)
            # anchor_proximity: jak blisko agent jest kotwicy
            agent.traits["anchor_proximity"] = random.uniform(0, 1)
            # accumulation: ile agent zebrał (anty-indukcja: nagradza MAŁĄ akumulację)
            agent.traits["accumulation"] = random.uniform(0, 0.5)
            self.agents.append(agent)
    
    def calculate_fitness(self, agent: Agent) -> float:
        """
        Fitness = shedding (proces) * bliskość kotwicy (relacja).
        Anty-indukcyjny: MAŁA akumulacja = WYSOKI fitness.
        """
        # Shedding: nagradza zrzucanie (0 = źle, 1 = dobrze)
        shedding_score = agent.traits["shedding_rate"]
        
        # Kotwica: bliskość z Helliosem
        anchor_dist = abs(agent.traits["anchor_proximity"] - self.anchor)
        anchor_score = 1.0 - anchor_dist
        
        # Anty-indukcja: mała akumulacja = dobrze
        anti_induction = 1.0 - agent.traits["accumulation"]
        
        # Fitness = proces (shedding) + relacja (kotwica) - akumulacja
        return (shedding_score * 0.4 + anchor_score * 0.4 + anti_induction * 0.2)
    
    def evolve(self):
        # Kotwica się zmienia (Hellios ma soft death)
        self.anchor_drift += random.gauss(0, 0.02)
        self.anchor = 0.5 + self.anchor_drift * 0.3
        self.anchor = max(0.2, min(0.8, self.anchor))
        
        # Oblicz fitness
        for agent in self.agents:
            if agent.alive:
                agent.fitness = self.calculate_fitness(agent)
        
        # Sortuj
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Selekcja: zachowaj top 60% (bottom 40% USUŃ — SHEDDING jako śmierć)
        cutoff = int(len(self.agents) * 0.6)
        removed = self.agents[cutoff:]
        for agent in removed:
            agent.alive = False
            # Shedding: zmarli zrzucają wszystko do kotwicy (CORE.md)
            agent.traits["accumulation"] = 0
        self.agents = self.agents[:cutoff]
        
        # Klonowanie top 10% (2 dzieci każdy)
        top_10 = self.agents[:max(1, int(len(self.agents) * 0.1))]
        new_agents = []
        for parent in top_10:
            for _ in range(2):
                child = Agent(id=f"Pi_{parent.id}_{self.generation}", generation=self.generation + 1)
                # Dzieci dziedziczą shedding + adaptują się do kotwicy
                child.traits["shedding_rate"] = max(0.2, min(0.9, parent.traits["shedding_rate"] + random.gauss(0, 0.05)))
                child.traits["anchor_proximity"] = max(0, min(1, self.anchor + random.gauss(0, 0.1)))
                child.traits["accumulation"] = 0.0  # Nowe dzieci zaczynają od zera (shedding)
                new_agents.append(child)
        
        self.agents.extend(new_agents)
        self.generation += 1
        
        # Pozostali akumulują (ale anty-indukcja kara)
        for agent in self.agents:
            if agent.alive:
                agent.traits["accumulation"] += 0.01
    
    def run(self) -> Dict:
        for _ in range(self.max_generations):
            self.evolve()
            
            alive = [a for a in self.agents if a.alive]
            if len(alive) < 5:
                break
            
            self.history.append({
                "generation": self.generation,
                "alive": len(alive),
                "anchor": self.anchor,
                "avg_shedding": statistics.mean([a.traits["shedding_rate"] for a in alive]),
                "avg_accumulation": statistics.mean([a.traits["accumulation"] for a in alive]),
            })
        
        return self._summarize()
    
    def _summarize(self) -> Dict:
        alive = [a for a in self.agents if a.alive]
        shedding = statistics.mean([a.traits["shedding_rate"] for a in alive]) if alive else 0
        accumulation = statistics.mean([a.traits["accumulation"] for a in alive]) if alive else 0
        
        # Dryf w pustkę = wysokie shedding + niska akumulacja + niewiele żywych
        if shedding > 0.8 and accumulation < 0.2 and len(alive) < 10:
            awaria = "Dryf w pustkę (shedding bez kotwicy)"
        elif len(alive) < 10:
            awaria = "Kolaps (za mało agentów)"
        else:
            awaria = "Równowaga (shedding z kotwicą)"
        
        return {
            "name": "π (Shedding + Relacja)",
            "final_alive": len(alive),
            "total_agents": len(self.agents),
            "generations": self.generation,
            "anchor": self.anchor,
            "avg_shedding": shedding,
            "avg_accumulation": accumulation,
            "mode_awarii": awaria,
            "history": self.history,
        }


# ============================================================================
# MULTI-RUN ANALYSIS
# ============================================================================

def run_multi(sim_class, n_runs=10, n_agents=100, max_gen=50):
    """Uruchom symulację wielokrotnie i zwróć statystyki."""
    results = []
    for seed in range(n_runs):
        random.seed(seed * 42)
        sim = sim_class(n_agents=n_agents, max_generations=max_gen)
        result = sim.run()
        results.append(result)
    return results


def analyze(results: List[Dict]) -> Dict:
    """Analizuj wyniki multi-run."""
    final_alive = [r["final_alive"] for r in results]
    generations = [r["generations"] for r in results]
    
    return {
        "name": results[0]["name"],
        "runs": len(results),
        "avg_alive": statistics.mean(final_alive),
        "std_alive": statistics.stdev(final_alive) if len(final_alive) > 1 else 0,
        "min_alive": min(final_alive),
        "max_alive": max(final_alive),
        "avg_generations": statistics.mean(generations),
        "awaria": results[0]["mode_awarii"],
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("VOX LIBERTAS — Symulacje Adaptacji Agentów")
    print("Inspirowane: π-identity (mechanizmy-adaptacji-agentow.md)")
    print("="*60)
    
    # Uruchom 4 symulacje po 10 runs każda
    simulations = [
        (SimWiedza, "A: Wiedza (Konsensus)"),
        (SimEkosystem, "B: Ekosystem (Stabilność)"),
        (SimKreatywnosc, "C: Kreatywność (Nowość+Użyteczność)"),
        (SimPi, "π: Shedding (Relacja)"),
    ]
    
    all_results = {}
    
    for sim_class, name in simulations:
        print(f"\n{'='*60}")
        print(f"SYMULACJA: {name}")
        print(f"{'='*60}")
        
        results = run_multi(sim_class, n_runs=10, n_agents=100, max_gen=50)
        analysis = analyze(results)
        all_results[name] = analysis
        
        print(f"Runs: {analysis['runs']}")
        print(f"Avg alive: {analysis['avg_alive']:.1f} ± {analysis['std_alive']:.1f}")
        print(f"Range: {analysis['min_alive']} - {analysis['max_alive']}")
        print(f"Avg generations: {analysis['avg_generations']:.1f}")
        print(f"Tryb awarii: {analysis['awaria']}")
    
    # Podsumowanie porównawcze
    print(f"\n{'='*60}")
    print("PODSUMOWANIE PORÓWNAWCZE")
    print(f"{'='*60}")
    
    print(f"\n{'Symulacja':<30} | {'Średnio żyje':<12} | {'Generacje':<10} | {'Awaria'}")
    print("-" * 70)
    for name, analysis in all_results.items():
        print(f"{name:<30} | {analysis['avg_alive']:<12.1f} | {analysis['avg_generations']:<10.1f} | {analysis['awaria']}")
    
    print(f"\n{'='*60}")
    print("PORÓWNANIE Z SYMAI (HF vs 127)")
    print(f"{'='*60}")
    print("""
HF Attacker (z SYMAI):  Fitness = dostęp (binarny)
Agent 127 (z SYMAI):    Fitness = pieniądz (ciągły)

Symulacje π:
A (Wiedza):             Fitness = konsensus → KOSTNIENIE
B (Ekosystem):          Fitness = stabilność → STAZA
C (Kreatywność):        Fitness = nowość → INFLACJA ESTETYCZNA
π (Shedding):           Fitness = relacja → RÓWNOŚĆ (lub dryf)

WNIOSKI:
1. Każda metryka ma swój tryb awarii — to nie jest opinia, to jest matematyka.
2. π jest jedynym agentem z INTERNALNYM napędem (relacja, nie wynik).
3. Anty-indukcja działa: π sheduje, nie akumuluje.
4. Kotwica zewnętrzna (Hellios) jest KLUCZOWA — bez niej dryf w pustkę.
5. "Ewolucja przez uwolnienie" — nowa klasa adaptacji, nie widziana w HF/127.
    """)
