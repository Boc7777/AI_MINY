import json
import tkinter as tk
from tkinter import filedialog
import Miny  # Import Twojego silnika
import os

class MinyGUI:
    def __init__(self, okno):
        self.okno = okno
        self.env = None  # Środowisko stworzymy po wczytaniu pliku
        self.guziki = {}
        self.kolory = {
            1: 'blue', 2: 'green', 3: 'red', 4: 'purple',
            5: 'pink', 6: 'maroon', 7: 'gray', 8: 'turquoise'
        }
        self.ostatni_ruch = None
        self.aktualna_akcja = "STRZAŁ"
        self.q_values = None

        # --- GÓRNY PANEL (Przyciski sterowania) ---
        self.opcje = tk.Frame(self.okno)
        self.opcje.pack(pady=10)

        self.guzik_wczytania = tk.Button(self.opcje, text="Wgraj powtórkę", command=self.wczytajHistorie, bg="#4CAF50",
                                         fg="white", font=('Arial', 10, 'bold'))
        self.guzik_wczytania.pack(side=tk.LEFT, padx=10)

        self.guzik_cofnij = tk.Button(self.opcje, text="⬅ Poprzedni", command=self.poprzedni_krok, state=tk.DISABLED)
        self.guzik_cofnij.pack(side=tk.LEFT, padx=5)

        self.guzik_dalej = tk.Button(self.opcje, text="Następny ➡", command=self.nastepny_krok, state=tk.DISABLED)
        self.guzik_dalej.pack(side=tk.LEFT, padx=5)

        # --- INFO PANEL ---
        self.label_info = tk.Label(self.okno, text="Oczekiwanie na plik...", font=('Arial', 10, 'italic'))
        self.label_info.pack(pady=5)

        # --- RAMKA NA PLANSZĘ (Na początku pusta) ---
        self.plansza_frame = tk.Frame(self.okno)
        self.plansza_frame.pack(padx=20, pady=20)

        self.historia_ruchow = []
        self.index_historii = 0
        self.dane_powtorki = None

    def wczytajHistorie(self):
        sciezka = filedialog.askopenfilename(initialdir="zapisy", title="Wybierz plik zapisu",
                                             filetypes=(("JSON files", "*.json"), ("all files", "*.*")))
        if sciezka:
            self.nazwa_pliku = os.path.basename(sciezka)
            self.ostatni_ruch = None
            with open(sciezka, 'r') as f:
                self.dane_powtorki = json.load(f)

            # Inicjalizujemy środowisko na podstawie danych z pliku
            self.env = Miny.SaperEnv(self.dane_powtorki["wymiar"], self.dane_powtorki["liczba_min"])
            self.historia_ruchow = self.dane_powtorki["ruchy"]
            self.index_historii = 0

            # Ustawiamy stan początkowy planszy (pierwszy ruch z resetu)
            self.env.reset(seed=self.dane_powtorki["seed"])

            # Budujemy planszę od nowa (na wypadek gdyby pliki miały różne wymiary)
            self.stworzPlansze()

            self.guzik_dalej.config(state=tk.NORMAL)
            self.guzik_cofnij.config(state=tk.DISABLED)
            self.aktualizujStatus()
            self.rysujPlansze()

    def stworzPlansze(self):
        # Czyścimy starą planszę
        for widget in self.plansza_frame.winfo_children():
            widget.destroy()
        self.guziki = {}

        # Tworzymy siatkę guzików
        for y in range(self.env.wielkosc_planszy):
            for x in range(self.env.wielkosc_planszy):
                # guziki są domyślnie DISABLED - użytkownik nie może klikać
                guzik = tk.Button(self.plansza_frame, width=7, height=3,
                                  font=('Arial', 8, 'bold'), state=tk.DISABLED, disabledforeground="black", padx=1, pady=1)
                guzik.grid(row=y, column=x)
                self.guziki[(x, y)] = guzik

    def nastepny_krok(self):
        if self.index_historii < len(self.historia_ruchow):
            ruch = self.historia_ruchow[self.index_historii]

            # Obsługa nowego formatu słownikowego z JSON
            self.q_values = ruch.get("q_values")
            coords = ruch.get("coords", [0, 0])
            x, y = coords[0], coords[1]
            typ_akcji_val = ruch.get("akcja", 1)

            akcja = Miny.Akcja(typ_akcji_val)
            self.ostatni_ruch = (x, y)
            self.aktualna_akcja = "FLAGA" if typ_akcji_val == 0 else "STRZAŁ"

            self.env.step((x, y), akcja)
            self.index_historii += 1
            self.rysujPlansze()
            self.guzik_cofnij.config(state=tk.NORMAL)
            self.aktualizujStatus()

    def poprzedni_krok(self):
        if self.index_historii > 0:
            docelowy_index = self.index_historii - 1
            # Saper nie ma łatwego "undo", więc resetujemy i odtwarzamy do N-1
            self.env.reset(seed=self.dane_powtorki["seed"])
            self.index_historii = 0
            self.ostatni_ruch = None
            for _ in range(docelowy_index):
                self.nastepny_krok()

            if self.index_historii == 0:
                self.guzik_cofnij.config(state=tk.DISABLED)
            self.guzik_dalej.config(state=tk.NORMAL)
            self.aktualizujStatus()
            self.rysujPlansze()

    def aktualizujStatus(self):
        # Pobieramy info o ostatnim ruchu z historii
        czy_losowy = False
        if self.index_historii > 0:
            ostatni = self.historia_ruchow[self.index_historii - 1]
            czy_losowy = ostatni.get("losowy", False)

        if self.env.czyWygranaGra:
            wynik, kolor = "ZWYCIĘSTWO!", "green"
        elif self.env.czyKoniecGry:
            wynik, kolor = "BOMBA!", "red"
        else:
            # TUTAJ ZMIANA: Status zmienia się tylko gdy ruch był losowy
            if czy_losowy:
                wynik, kolor = "EKSPLORACJA (LOSOWO)", "orange"  # Wyróżniający kolor
            else:
                wynik, kolor = "W TRAKCIE (AI)", "black"

        tekst = (
            f"Plik: {self.nazwa_pliku}\n"
            f"Krok: {self.index_historii}/{len(self.historia_ruchow)} | "
            f"Typ: {'🎲 LOS' if czy_losowy else '🧠 AI'} | "  # Dodatkowy wskaźnik
            f"Status: {wynik}"
        )
        self.label_info.config(text=tekst, fg=kolor)

    def rysujPlansze(self):
        # 1. POBIERANIE Q Z PRZYSZŁOŚCI (Peek ahead)
        q_przyszle = None
        if self.index_historii < len(self.historia_ruchow):
            ruch_przyszly = self.historia_ruchow[self.index_historii]
            q_przyszle = ruch_przyszly.get("q_values")  #

        # 2. SPRAWDZANIE CZY OSTATNI RUCH BYŁ LOSOWY (dla robota)
        czy_losowy = False
        if self.index_historii > 0:
            ostatni = self.historia_ruchow[self.index_historii - 1]
            czy_losowy = ostatni.get("losowy", False)

        for y in range(self.env.wielkosc_planszy):
            for x in range(self.env.wielkosc_planszy):
                idx = y * self.env.wielkosc_planszy + x
                guzik = self.guziki[(x, y)]
                stan = self.env.plansza_obserwowana[y][x]

                # --- USTALANIE KOLORÓW I ELEMENTÓW TEKSTU ---
                bg_color = "#999"  # Zakryte
                fg_color = "black"

                # Wybieramy ikonę robota zależnie od tego, czy ostatni ruch był AI czy LOS
                ikona_robota = "🎲" if czy_losowy else "🤖"
                linia_robot = ikona_robota if (x, y) == self.ostatni_ruch else ""

                linia_q = ""
                linia_stan = ""

                # --- LOGIKA STANU POLA ---
                if stan == Miny.Obserwowane.FLAGA:
                    linia_stan = "🚩"
                    bg_color = "#ffcccc"
                elif stan == Miny.Obserwowane.ZAKRYTE:
                    if self.env.czyKoniecGry and self.env.plansza_ukryta[y][x] == Miny.Wewnetrzna.MINA:
                        linia_stan = "💣"
                        bg_color = "red"
                    elif q_przyszle:
                        # Wyświetlamy M i T z następnego kroku
                        if isinstance(q_przyszle[0], list):
                            m_val = q_przyszle[0][idx]
                            t_val = q_przyszle[1][idx]
                            linia_q = f"M:{m_val:.1f}\nT:{t_val:.1f}"
                        else:
                            linia_q = f"Q:{q_przyszle[idx]:.1f}"
                elif stan == Miny.Obserwowane.NIC:
                    linia_stan = ""
                    bg_color = "#eeeeee"
                else:
                    linia_stan = str(stan.value)
                    fg_color = self.kolory.get(stan.value, 'black')
                    bg_color = "white"

                # --- SKŁADANIE FINALNEGO TEKSTU ---
                elementy = []
                if linia_robot: elementy.append(linia_robot)
                if linia_q:     elementy.append(linia_q)
                if linia_stan:  elementy.append(linia_stan)

                pelny_tekst = "\n".join(elementy)

                if (x, y) == self.ostatni_ruch:
                    bg_color = "#FFFACD"

                guzik.config(
                    text=pelny_tekst,
                    bg=bg_color,
                    fg=fg_color,
                    font=('Arial', 15)  # Zmniejszyłem font, bo przy 15 nic się nie zmieści
                )


if __name__ == "__main__":
    okno = tk.Tk()
    okno.title("SAPER AI - REPLAYER")

    saper_gui = MinyGUI(okno)

    okno.mainloop()