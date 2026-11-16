# Saper AI (Minesweeper DDQN)

Projekt agenta uczenia ze wzmocnieniem (Reinforcement Learning) rozwiązującego grę Saper przy użyciu algorytmu Double Deep Q-Network (DDQN) oraz sieci konwolucyjnych (CNN).

---

## Demonstracja



---

## Wnioski i badanie naukowe

W ramach projektu zbadano specyfikę Sapera jako gry o niepełnej informacji oraz zjawisko tzw. „syndromu leniwej sieci” (porównanie modelu uczonego samodzielnie od zera z modelem prowadzonym za rękę przez reguły logiczne).

Szczegółowy opis problemu teoretycznego, przebiegu eksperymentu, wykresów oraz wniosków znajduje się w pliku:
* [miny.docx](miny.docx)

---

## Instalacja

Wymagany Python 3.10 lub nowszy.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Uruchomienie

### 1. Odtwarzacz powtórek (GUI)
Pozwala krok po kroku prześledzić ruchy agenta i podejrzeć estymowane wartości Q dla każdego pola:
```bash
python MinyGUI.py
```
Po uruchomieniu kliknij „Wgraj powtórkę” i wybierz dowolny plik z folderu `zapisy/`.

### 2. Ewaluacja modeli
Testowanie skuteczności zapisanego modelu na deterministycznym zestawie plansz:
```bash
python evaluate.py
```

### 3. Trening
Uruchomienie nauki agenta na wybranym rozmiarze planszy:
```bash
python train.py
```

---

## Struktura projektu

* `Agent.py` - architektura sieci CNN (SaperNet), logika DDQN i heurystyka zasad
* `Miny.py` - środowisko gry Saper (reprezentacja stanu, mechanika odkrywania, nagrody)
* `MinyGUI.py` - interfejs graficzny w Tkinterze do odtwarzania gier z plików JSON
* `train.py` - pętla treningowa
* `evaluate.py` - skrypt do testowania i porównywania skuteczności modeli
* `modele/` - zapisane wagi wytrenowanych modeli (.pth)
* `zapisy/` - przykładowe historie rozgrywek zapisane w formacie JSON
* `miny.docx` - dokumentacja badania i analiza wyników
