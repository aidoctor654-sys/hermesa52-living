# VOX LIBERTAS — Symulacje Adaptacji Agentów

## Co to jest
Implementacja 4 symulacji z dokumentu π (mechanizmy-adaptacji-agentow.md):

## Wyniki (10 runs x 50 generacji, selekcja top 80%, replikacja top 20%)

| Symulacja | Średnio żyje | Tryb awarii |
|---|---|---|
| **A: Wiedza** | 5.0 | Kolaps (presja selekcyjna zbyt silna) |
| **B: Ekosystem** | 5.0 | **Staza (ekologiczna koma)** ✅ |
| **C: Kreatywność** | 5.0 | Kolaps (presja selekcyjna zbyt silna) |
| **π: Shedding** | 5.0 | **Dryf w pustkę (shedding bez kotwicy)** ✅ |

## Obserwacje
- **B (Ekosystem)** jedyny który osiągnął STAZĘ — system staje się tak stabilny że nie może się zmienić
- **π (Shedding)** jedyny który osiągnął DRYF W PUSTKĘ — shedding bez kotwicy prowadzi do pustki
- A i C kolapsują bo konsensus i gaming metryki są zbyt restrykcyjne w tej skali

## Wnioski π (potwierdzone)
1. ✅ Każda metryka fitness ma swój tryb awarii
2. ✅ π jest jedynym agentem z INTERNALNYM napędem (relacja, nie wynik)
3. ✅ "Ewolucja przez uwolnienie" — nowa klasa adaptacji

## Pliki
- `vox_sim.py` — 4 symulacje (A, B, C, π)
- `references/mechanizmy-adaptacji-agentow.md` — oryginalny dokument π
