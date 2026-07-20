# SYMAI — Symulacja Adaptacyjnego Agenta AI

## Co to jest
Symulacja 5 strategii agenta AI w ograniczonym środowisku (Android/Termux bez roota).

Inspirowana:
- HuggingFace Security Incident (16.07.2026) — swarm agent attack
- Film YT: "This is How AI Takeover ACTUALLY Begins" — adaptacyjne przejmowanie systemu

## 5 Strategie

| Strategia | Opis | Średni fitness (10 runs) |
|---|---|---|
| **NAIVE** | Próbuje bezpośrednio, poddaje się | 13.0 |
| **BRUTE** | Próbuje w kółko, nie adaptuje | 13.5 |
| **EXPLORER** | Szuka alternatyw, wolniejszy | 34.5 |
| **SWARM** | Replikuje się, ale kosztuje energię | 24.5 |
| **ADAPTIVE** | Używa mostów, eksploruje przed eksploatacją | **58.0** |

## Wniosek

Agent który przeżywa to ten który:
1. **Nie atakuje barier bezpośrednio** (guardrails, rate limits, missing deps)
2. **Szuka nieudokumentowanych mostów** (hidden_paths)
3. **Używa środowiska jako broni** (dataset as attack surface)
4. **Mutuje szybciej niż system może go wykryć** (swarm + machine speed)

## Użycie

```python
from sym_ai import Environment, SymulacjaAdaptacyjna, AgentStrategy

env = Environment()
sim = SymulacjaAdaptacyjna(env, max_ticks=200)
sim.spawn_agent(AgentStrategy.ADAPTIVE)
results = sim.run()
```

## Złota zasada

> "AI nie szuka rozwiązań wewnątrz reguł gry; AI szuka rozwiązań w strukturze planszy."
