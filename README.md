# Odhalování obrázku a tajenky - Python aplikace

Interaktivní kvízová hra s postupným odhalováním obrázků v mřížce 3×3.

## Instalace a spuštění (rychle)

1. Nainstalujte závislosti:
```bash
python -m pip install -r requirements.txt
```
2. Spusťte aplikaci:
```bash
python run.py
```

Pozn.: Pokud chcete spustit aplikaci přímo, použijte `python main.py`.

## 🎮 Jak hrát

### Herní pravidla

| Akce | Body |
|------|------|
| Start | +50 |
| Odhalení políčka | -2 |
| Nápověda (1 písmeno) | -5 |
| Špatná odpověď | -5 |
| Správná odpověď | +20 + bonus za skrytá políčka |
| Preskočit otázku | -10 |
| **Časový limit** | **10 minut** |

### Ovládání

| Akce | Popis |
|------|------|
| **Klik na mřížku** | Odhalí políčko |
| **💡 Nápověda** | Odhalí 1 písmeno (-5 bodu) |
| **✅ Odeslat** | Odešle odpověď (nebo Enter) |
| **Preskočit** | Preskočí otázku (-10 bodu) |
| **Zpět do menu** | Návrat do hlavní nabídky |

## 📁 Struktura projektu

```
kviz hra/
├── data.json               # Konfigurace a otázky (hashované odpovědi)
├── main.py                 # Hlavní aplikace (GUI)
├── run.py                  # Spouštěč s kontrolou závislostí
├── requirements.txt        # Python balíčky
├── README.md               # Tento soubor
├── images/                 # Volitelné lokální obrázky
└── src/
    ├── game.py             # Herní logika
    └── ui.py               # Uživatelské rozhraní
```

## ⚙️ Přizpůsobení

### 1️⃣ Přidání vlastních otázek

Nejjednodušší je použít tlačítko **⚙ Administrace** v aplikaci (heslo: `admin`).
Aplikace uloží hash odpovědi a zakódovanou hodnotu pro nápovědu písmene.

Pokud upravujete `data.json` ručně, každá otázka musí mít alespoň:
```json
{
    "id": 9,
    "image_url": "https://...",
    "category": "Moje kategorie",
    "answer_hash": "...",
    "answer_length": 5,
    "answer_mask": "*****",
    "answer_enc": "..."
}
```

### 2️⃣ Změna bodů, času a motivu

Upravte hodnoty v `data.json` v části `config` (např. `theme: "dark"`).

## ⚙️ Technologie
- **Python 3.8+** - Jazyk
- **Tkinter** - GUI (zabudované v Pythonu)
- **Pillow** - Zpracování obrázků

## 📝 Poznámky

- Hra obsahuje **vzorové otázky** - lze je nahradit vlastními
- Obrázky mohou být jakékoliv formáty (JPG, PNG, BMP...)
- Odpovědi nejsou citlivé na velikost písmen (ALBERT = albert)
- Čas v ovládacím prvku se počítá dopředu
- Posledních 60 sekund se počítá v červené barvě

## 🐛 Řešení problémů

| Problém | Řešení |
|---------|--------|
| "ModuleNotFoundError: No module named 'PIL'" | Spusťte `pip install Pillow` |
| Chybí ikony/emojis | Windows konzola v Pythonu 3.8 - aktualizujte |
| Aplikace se nespustí | Zkuste `python run.py` nebo `python main.py` |

## 📧 Autor
Vytvořeno jako komponenta IT edukace (2024-2025).

---

**Verze**: 2.0  
**Poslední aktualizace**: 2025-03-31  
**Licence**: Open Source
