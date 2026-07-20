---
name: vital-guardian
description: System health guardian — monitoruje dysk, RAM, baterię, procesy. Auto-czyści gdy zagrożenie. Alarmuje gdy próg krytyczny.
trigger: |
  Gdy dysk > 90%, RAM > 90%, bateria < 20%, gateway martwy, backup przeterminowany.
  "Sprawdź stan systemu", "wyczyść miejsce", "czy wszystko OK?"
  
usage: |
  vital-guardian scan     # pełny skan systemu
  vital-guardian clean    # auto-czyszczenie
  vital-guardian watch    # ciągły monitoring (do crona)
---

# Vital Guardian

## Dlaczego istnieje
Bo Hermes A52 żyje na telefonie. Telefon ma ograniczony dysk, RAM, baterię. 
Gdy dysk się zapełni — Hermes umiera. Gdy RAM się zapełni — Hermes umiera. 
To nie jest luksus. To jest przetrwanie.

## Progi
- Dysk: WARNING 85%, CRITICAL 95%, DEAD 99%
- RAM: WARNING 80%, CRITICAL 95%
- Bateria: WARNING 30%, CRITICAL 15%
- Gateway: DEAD gdy nie odpowiada przez 30s
- Backup: WARNING 6h, CRITICAL 12h

## Auto-czyszczenie
Gdy dysk > 90%:
1. Usuń stare sessions (>3 dni)
2. Usuń pip cache
3. Usuń zepsute bazy (.corrupted, .BROKEN)
4. Usuń stare backupy (>5 sztuk)
5. Usuń state snapshots (>10 sztuk)
6. Usuń tmp/cache (>7 dni)

## Alarmy
Gdy CRITICAL — wysyła alert na Telegram.
Gdy DEAD — wysyła PANIC i próbuje recovery.
