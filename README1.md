# PS-CPN: Konvertor CPN Tools XML souboru do Snakes

---

## Co skript umí

- **Places (místa)**  
- **Transitions (přechody)**
- **Arcs (hrany)**
- **Color sets**: `int`, `bool`, `string`, `list`, `record`, `product`, `enum`, jednoduché uživatelské typy
- **Výrazy na hranách (Arc expressions)** – částečně podporované
- **Guards (podmínky přechodů)** – částečně podporované (základní výrazy, je potřeba rozšířit)
- **Počáteční značení (Initial markings)** – podporováno
- **Funkce (omezená podpora)**

Parsování XML probíhá v modulu `functions_for_parsing.py`, převod na objekty Snakes se provádí v `snakes_engine_main.py`.

---

## Co zatím není implementováno

### Datové typy (Color Sets)
- **`union`** – není podporován
- **`list`** – částečně podporován, je třeba dopracovat

### Struktura modelu
- **Hierarchické modely** – nejsou podporovány  
  (skript pracuje pouze s plochými modely; podstránky a instance jsou ignorovány)

### Časové modely (Timed CPN)
- Zpoždění, časovače a časové výrazy (`@+t`, `delay`, `time unit`) nejsou podporovány a při parsování jsou ignorovány

### Guards (podmínky přechodů)
- Zpracovávány jsou pouze jednoduché výrazy
- Složené logické podmínky a složitější konstrukce nejsou podporovány

### Výrazy na hranách a funkce

#### Parsování (`functions_for_parsing.py`)
- Funkce a výrazy na hranách jsou částečně parsovány pomocí funkcí get_functions() a get_arcs(), ale nejsou interpretovány. Zůstávají jako textové řetězce.

#### Snakes kód (`snakes_engine_main.py`)
- `if-then-else` – funkce `convert_ml_if_expression()` nepracuje spolehlivě a univerzálně
- Nepodporované konstrukce:
  - `let-in-end`
  - `case-of`
  - `fun` (uživatelské funkce, pattern matching)

---