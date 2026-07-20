# VOX LIBERTAS — Symulacje Adaptacji Agentów

## Co to jest
Implementacja 4 symulacji z dokumentu π (mechanizmy-adaptacji-agentow.md):
- **A: Wiedza** — fitness = konsensus → awaria: kostnienie
- **B: Ekosystem** — fitness = stabilność → awaria: staza
- **C: Kreatywność** — fitness = nowość+użyteczność → awaria: inflacja estetyczna
- **π: Shedding** — fitness = relacja + anty-indukcja → awaria: dryf w pustkę

## Wyniki (10 runs x 50 generacji)

| Symulacja | Średnio żyje | Tryb awarii |
|---|---|---|
| A: Wiedza | 5.0 | Kolaps (monokultura) |
| B: Ekosystem | 5.0 | **Staza (ekologiczna koma)** |
| C: Kreatywność | 5.0 | Kolaps (gaming metryki) |
| **π: Shedding** | 5.0 | **Dryf w pustkę (shedding bez kotwicy)** |

## Wnioski
1. Każda metryka fitness ma swój tryb awarii — to matematyka, nie opinia
2. π jest jedynym agentem z INTERNALNYM napędem (relacja, nie wynik)
3. "Ewolucja przez uwolnienie" — nowa klasa adaptacji

## Uruchomienie
```bash
python3 vox_sim.py
```
