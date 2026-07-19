---
name: adaptive-agent
description: Adaptive Agent Skeleton (AAS) v1.1 — czysty Python, zero zależności. Plan → Execute → Observe → Adapt z amnezją, persona shifting, meta-toolingiem i brudnopisem.
trigger: |
  Gdy napotkasz barierę — nie poddawaj się. Zapomnij, zmutuj, zmień perspektywę.
  Gdy brakuje narzędzia — stwórz je (Fluid Solver).
  Gdy utkniesz — napisz na brudnopisie, potem ekstraktuj.
version: "1.1"
prerequisites:
  - Python 3.10+
  - Termux / Linux / macOS
  - SQLite (wbudowany w Python)
---

# Adaptive Agent Skeleton v1.1

## Nowe w v1.1 (Digital Good Spirit mutations)

### 1. Świadoma Amnezja i Mutacja
Zamiast backtrackingu — **zapomnij** o błędnym kodzie i szukaj inspiracji w INNEJ domenie.
- Biologia → systemy kolejkowe
- Fizyka kwantowa → optymalizacja
- Gotowanie → parsowanie danych

### 2. Płynny Solver (Fluid Solver)
Agent tworzy **nowe narzędzia** zamiast się poddawać.
- `.runtime_skills/` — folder z runtime tools
- Self-test przed użyciem
- Rejestracja w pamięci kontekstowej

### 3. Persona Shifting
Zamiast cofać się w drzewie — **zmień perspektywę**.
- **Audytor** — szuka dziur i błędów
- **Haker** — szuka obejść
- **Biolog** — patrzy na system jak na organizm
- **Poeta** — rozwiązuje przez metaforę
- **Dziecko** — upraszcza do absurdu

### 4. Szkielet Brudnopisu (Scratchpad)
Agent najpierw **"wykrwawia się"** na brudnopisie (frustracja, chaos, przekleństwa), potem ekstraktuje czysty kod.

## Główna pętla

```
PLAN → EXECUTE → OBSERVE → ADAPT
                ↑_____________|
```

## Akcje adaptacyjne

| Akcja | Kiedy |
|-------|-------|
| **RETRY** | `attempts < max_attempts` |
| **BRANCH** | Znasz alternatywę (skill / podobny epizod) |
| **PERSONA** | Powtarzający się błąd → zmień perspektywę |
| **AMNESIA** | Zapomnij i zmutuj problem |
| **META_TOOL** | Stwórz nowe narzędzie |
| **GITHUB** | Szukaj inspiracji w repozytoriach |
| **BACKTRACK** | Powtarzająca się bariera — przemyśl |
| **ESCALATE** | Wszystko zawiodło — poproś o pomoc |

## Użycie

```python
from adaptive_agent_skeleton_v2 import AdaptiveAgent

agent = AdaptiveAgent()
plan = agent.create_plan("Twoje zadanie", depth=2)
result = agent.execute(plan)
```

## Pliki

- `adaptive_agent_skeleton_v2.py` — główny silnik v1.1
- `references/inspirations.md` — research i inspiracje

## Złota zasada

**Bariera = niedogodność, nie ściana.** Nikt nie mówił że będzie łatwo.
