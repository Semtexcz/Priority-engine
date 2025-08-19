# Priority Engine

**Priority Engine** je nástroj pro chytrou prioritizaci úkolů.  
Kombinuje několik osvědčených metodik:

- **Eisenhowerova matice** (urgentní × důležité),
- **Vrstvení backlogu** (Fundamenty, Strategické projekty, Podpůrné úkoly, Volnočas/experimenty),
- **Skórování dopadu, náročnosti a urgence**,  
- **Denní výběr MIT (Most Important Tasks)**.

Cílem je zbavit se zahlcení stovkami úkolů, ale neztratit kreativitu a dlouhodobé cíle z dohledu.

---

## 🚀 Instalace

Projekt používá [Poetry](https://python-poetry.org/).

### Lokální instalace (pro vývoj)

```bash
git clone https://github.com/Semtexcz/Priority-engine
cd priority-engine
poetry install
```

Po instalaci bude dostupný příkaz:

```bash
poetry run prio --help
```

---

### Globální instalace pomocí [pipx](https://github.com/pypa/pipx)

Pokud chceš nástroj používat jako běžný příkaz v systému:

```bash
pipx install git+https://github.com/Semtexcz/Priority-engine
```

Po úspěšné instalaci spustíš příkaz odkudkoliv:

```bash
prio --help
```

Pokud budeš chtít projekt aktualizovat:

```bash
pipx upgrade priority-engine
```



## 📦 Struktura projektu

```
src/priority_engine
├── cli.py          # CLI (click) – příkazy process, template
├── models.py       # Doménová entita Task
├── policies.py     # Politiky vrstev, urgence, Eisenhower classifier
├── scoring.py      # Strategie skórování
├── repositories.py # Načítání a ukládání (CSV, JSON)
├── services.py     # Aplikační logika (prefilter, výpočty, engine)
├── selectors.py    # Výběr MIT úkolů
├── sorters.py      # Řazení backlogu
└── __init__.py
```

## 🗂 Architektura a moduly

Projekt je navržen podle principů **OOP** a **SOLID** pro snadnou rozšiřitelnost a čitelnost. Každý modul má jasně definovanou zodpovědnost:

* **`cli.py`** – vstupní bod aplikace. Definuje příkazovou řádku pomocí knihovny `click` a propojuje uživatele s aplikační logikou.
* **`models.py`** – obsahuje doménové modely, zejména datovou třídu `Task`, která reprezentuje úkol a jeho atributy (název, deadline, skóre atd.).
* **`repositories.py`** – zajišťuje načítání a ukládání dat, např. práci s CSV soubory. Odděluje I/O logiku od zbytku aplikace.
* **`scoring.py`** – implementuje algoritmus pro výpočet skóre úkolů na základě dopadu, páky, náročnosti a dalších kritérií.
* **`sorters.py`** – obsahuje strategii řazení úkolů podle vypočítaného skóre a dalších pravidel (např. deadline, energie).
* **`selectors.py`** – logika pro výběr MIT (Most Important Tasks) – denního výběru nejdůležitějších úkolů.
* **`services.py`** – aplikační logika, která orchestruje načtení dat z `repositories`, výpočet skóre, řazení a výběr MIT.
* **`policies.py`** – definice pravidel a politik (např. pravidla pro vrstvy backlogu, co má přednost při konfliktu, jak zacházet s delegovanými úkoly).



---

## ⚡ Použití

### 1. Vytvoření šablony

Vytvoř ukázkový CSV s několika úkoly:

```bash
poetry run prio template --out tasks.csv
```

### 2. Zpracování backlogu

```bash
poetry run prio process --in tasks.csv --out prioritized.csv --mits-out mits.md
```

* `--in` vstupní CSV nebo JSON se seznamem úkolů
* `--out` CSV s vypočtenými prioritami a seřazením
* `--mits-out` volitelný soubor s denními MIT v Markdownu
* `--today` YYYY-MM-DD pro simulaci jiného data (např. při testech)
* `--alpha` parametr skórovací funkce (default 0.7)

### 3. Výsledky

* `prioritized.csv` obsahuje:

  * výpočet skóre,
  * kvadrant Eisenhowera,
  * štítek (HighROI, BigBet, QuickWin),
  * další metriky.
* `mits.md` obsahuje přehled 1–3 nejdůležitějších úkolů dne.

---

## 🧮 Vstupní formát

Priority Engine pracuje s jednoduchým tabulkovým formátem (CSV/JSON).
CSV musí mít hlavičku:

```csv
Title,Owner,Deadline,TimeEst,Energy,Layer,Impact,Leverage,Effort,Notes
```

### Popis jednotlivých polí:

* **Title** *(string, povinné)*
  Název úkolu nebo aktivity. Měl by být krátký, jasný a akční.
  *Příklad:* `"Nastavit zálohování databáze"`, `"Domluvit prohlídku u doktora"`

* **Owner** *(string, default = "já")*
  Osoba zodpovědná za úkol.

  * Pokud je hodnota `já`, úkol se počítá mezi tvoje úkoly.
  * Pokud je jiný text (např. `"Karel"`), systém úkol **automaticky přesune do kategorie „Delegováno“**.
    *Příklad:* `"já"`, `"Karel"`, `"Externí firma"`

* **Deadline** *(date, volitelné)*
  Datum, do kdy má být úkol dokončen, ve formátu `YYYY-MM-DD`.
  Deadline ovlivňuje **urgentnost** a tím skóre úkolu.

  * Pokud není uveden, úkol není urgentní.
    *Příklad:* `"2025-09-15"`, `""` (prázdné pole = bez deadline)

* **TimeEst** *(float, default = 1.0)*
  Odhad času v hodinách, kolik zabere splnění úkolu.
  Slouží pro klasifikaci typu úkolu (např. **Quick Win** ≤ 0.5h).
  *Příklad:* `0.25` (15 minut), `1.5` (1,5 hodiny), `6` (celý den)

* **Energy** *(enum: low | medium | high, default = medium)*
  Úroveň energie, kterou úkol vyžaduje.
  Hodí se pro plánování dne – náročné úkoly (high) dělat ráno, rutinní (low) na konec dne.
  *Příklad:* `"low"` = uklidit stůl, `"high"` = psát kapitolu knihy

* **Layer** *(enum: Fundament | Strategic | Support | Leisure)*
  Vrstva, do které úkol patří:

  * **Fundament** – základní věci (zdraví, rodina, finance, práce)
    *Příklad:* `"Jít na fyzioterapii"`, `"Zaplatit nájem"`
  * **Strategic** – dlouhodobé projekty, které tě posouvají dopředu
    *Příklad:* `"Napsat kapitolu do kurzu"`, `"Stavba sauny"`
  * **Support** – organizační a pomocné úkoly
    *Příklad:* `"Uklidit workspace"`, `"Zorganizovat meeting"`
  * **Leisure** – volnočasové a experimentální nápady
    *Příklad:* `"Vyzkoušet nový framework"`, `"Přečíst článek o AI"`

* **Impact** *(int 0–5)*
  Hodnocení dopadu – jak moc úkol přispívá k tvým hodnotám a cílům.

  * `0` = žádný přínos
  * `5` = zásadní posun
    *Příklad:* `5` = „Spustit nový kurz“, `1` = „Upravit barvu tlačítka na webu“

* **Leverage** *(int 0–5)*
  Hodnocení okamžitosti / páky – násobí úkol výsledky, otevírá dveře, využívá příležitost.

  * `0` = žádný multiplikační efekt
  * `5` = extrémní páka (odemyká mnoho dalších kroků)
    *Příklad:* `5` = „Automatizovat zálohy“ (šetří čas každý den), `2` = „Dokončit jednorázovou drobnost“

* **Effort** *(int 1–5)*
  Subjektivní náročnost – jak těžké to je časově, mentálně, organizačně.

  * `1` = téměř nic (klik, krátký telefonát)
  * `5` = extrémně náročný projekt
    *Příklad:* `1` = „Odpovědět na e-mail“, `4` = „Naplánovat dovolenou pro 10 lidí“

* **Notes** *(string, volitelné)*
  Libovolné poznámky, kontext, odkazy nebo doplňující info.
  *Příklad:* `"Použít Rclone + cron"`, `"Link na dokumentaci: ..."`

---

## ✍️ Ukázkový CSV soubor

```csv
Title,Owner,Deadline,TimeEst,Energy,Layer,Impact,Leverage,Effort,Notes
"Nastavit zálohy","já",,0.5,medium,Fundament,4,3,2,"Rclone + cron"
"Napsat skript","já",2025-09-10,1,high,Strategic,5,4,2,"Automatizace"
"Uklidit plochu","já",,0.25,low,Support,2,2,1,""
"Přečíst článek","já",,1,low,Leisure,1,1,2,"Zajímavost z HackerNews"
```

---

Chceš, abych ti k tomu ještě dopsal i **příklady JSON vstupu** (ve formátu seznamu objektů nebo `{"tasks": [...]}`), aby bylo README úplně kompletní?


## 🧮 Vstupní formát

CSV hlavička:

```csv
Title,Owner,Deadline,TimeEst,Energy,Layer,Impact,Leverage,Effort,Notes
```

* **Title** – název úkolu
* **Owner** – kdo je zodpovědný (pokud není „já“, úkol se deleguje)
* **Deadline** – datum ve formátu YYYY-MM-DD (volitelné)
* **TimeEst** – odhad času (v hodinách, float)
* **Energy** – low / medium / high
* **Layer** – Fundament | Strategic | Support | Leisure
* **Impact** – dopad (0–5)
* **Leverage** – okamžitost / páka (0–5)
* **Effort** – náročnost (1–5)
* **Notes** – volitelný komentář

JSON formát: seznam objektů se stejnými klíči.

---

## 🛠️ Princip algoritmu

1. **Prefilter** – delegace a archivace zbytečných úkolů.
2. **Výpočet skóre**

   ```
   Score = (ImportanceCore * UrgencyMultiplier) / (Effort ^ alpha)
   ```

   kde:

   * ImportanceCore = kombinace Impact + Leverage + LayerWeight
   * UrgencyMultiplier = roste s blížícím se deadlinem
   * alpha (default 0.7) tlumí vliv Effort.
3. **Eisenhower** – určení kvadrantu (urgentní × důležité).
4. **Tagging** – QuickWin, HighROI, BigBet.
5. **Řazení** – podle Score (desc), deadline (asc), impact (desc).
6. **MIT výběr** – max 3 úkoly:

   * 1× Fundament,
   * 1× Strategic (ideálně BigBet),
   * 1× HighROI nebo QuickWin.

---

Jasně, můžeš do README přidat třeba takovýto odstavec k API:

---

## 🌐 REST API

Součástí projektu je i REST API postavené na [FastAPI](https://fastapi.tiangolo.com/).
API poskytuje endpoint `/process-file`, který umožňuje nahrát CSV nebo JSON soubor s úkoly, automaticky je zpracovat a vrátit výsledek včetně vypočtených priorit a doporučených „Most Important Tasks (MITs)“. Parametry zpracování (např. váha `alpha` nebo aktuální datum) lze nastavit pomocí query/form parametrů. Výstup je vracen ve formátu JSON a je tak snadno využitelný v dalších aplikacích nebo integračních scénářích.

Server lze spustit příkazem:

```bash
poetry run uvicorn priority_engine.api.main:app --reload
```

Poté bude dostupná interaktivní dokumentace na adrese [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

Chceš, abych ti tam ještě přidal i příklad **curl** požadavku s nahráním CSV souboru?


## 📖 Příklad

### Vstup (`tasks.csv`)

```csv
Title,Owner,Deadline,TimeEst,Energy,Layer,Impact,Leverage,Effort,Notes
"Nastavit zálohy","já",,0.5,medium,Fundament,4,3,2,"Rclone + cron"
"Napsat skript","já",2025-08-25,1,high,Strategic,5,4,2,"Automatizace"
"Uklidit plochu","já",,0.25,low,Support,2,2,1,""
"Přečíst článek","já",,1,low,Leisure,1,1,2,"zajímavost"
```

### Výstup (`prioritized.csv`)

Obsahuje výpočet Score, Quadrant, Tag atd.

### MIT (`mits.md`)

<!-- ```markdown -->
# Dnešní MIT (Most Important Tasks)

## 1. Nastavit zálohy
- Layer: **Fundament** | Tag: **HighROI** | Quadrant: **Important+NotUrgent**
- Score: **7.21** | TimeEst: **0.5 h** | Effort: **2** | Impact: **4** | Leverage: **3**
- Poznámky: Rclone + cron
<!-- ``` -->

---

## 🧑‍💻 Vývoj

Struktura kódu je rozdělena dle SOLID principů:

* Politiky (vrstvy, urgence, klasifikace) lze snadno rozšířit.
* Skórovací strategie je injektovatelná.
* CLI (`cli.py`) je oddělené od jádra.

---

## 📜 Licence

MIT License © 2025 [Daniel Kopecký](mailto:kopecky.d@gmail.com)
