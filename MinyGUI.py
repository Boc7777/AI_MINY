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
                guzik = tk.Button(self.plansza_frame, width=3, height=1,
                                  font=('Arial', 12, 'bold'), state=tk.DISABLED, disabledforeground="black")
                guzik.grid(row=y, column=x)
                self.guziki[(x, y)] = guzik

    def nastepny_krok(self):
        if self.index_historii < len(self.historia_ruchow):
            ruch = self.historia_ruchow[self.index_historii]

            x = ruch[0]
            y = ruch[1]
            typ_akcji_val = ruch[2] if len(ruch) > 2 else 1
            akcja = Miny.Akcja(typ_akcji_val)

            self.ostatni_ruch = (x, y)

            if typ_akcji_val == 0:
                self.aktualna_akcja = "FLAGA"
            else:
                self.aktualna_akcja = "STRZAŁ"

            self.env.step((x, y), akcja)

            self.index_historii += 1
            self.rysujPlansze()
            self.guzik_cofnij.config(state=tk.NORMAL)
            self.aktualizujStatus()

            if self.index_historii == len(self.historia_ruchow) or self.env.czyKoniecGry:
                self.guzik_dalej.config(state=tk.DISABLED)

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
        if self.env.czyWygranaGra:
            wynik = "ZWYCIĘSTWO!"
            kolor = "green"
        elif self.env.czyKoniecGry:
            wynik = "BOMBA!"
            kolor = "red"
        else:
            wynik = "W TRAKCIE"
            kolor = "black"

        tekst = (
            f"Plik: {self.nazwa_pliku}\n"
            f"Krok: {self.index_historii}/{len(self.historia_ruchow)} | "
            f"Ostatnia akcja: {self.aktualna_akcja} | "
            f"Status: {wynik}"
        )

        self.label_info.config(text=tekst, fg=kolor)

    def rysujPlansze(self):
        for y in range(self.env.wielkosc_planszy):
            for x in range(self.env.wielkosc_planszy):
                guzik = self.guziki[(x, y)]
                stan = self.env.plansza_obserwowana[y][x]
                if stan == Miny.Obserwowane.FLAGA:
                    guzik.config(text="🚩", bg="#ffcccc")
                elif stan == Miny.Obserwowane.ZAKRYTE:
                    # Pokazujemy bomby tylko po przegranej
                    if self.env.czyKoniecGry and self.env.plansza_ukryta[y][x] == Miny.Wewnetrzna.MINA:
                        guzik.config(text="💣", bg="red")
                    else:
                        guzik.config(text="", bg="#bbb")
                elif stan == Miny.Obserwowane.NIC:
                    guzik.config(text="", bg="#eeeeee")
                else:
                    kolor = self.kolory.get(stan.value, 'black')
                    guzik.config(text=str(stan.value), fg=kolor, bg="white")

                if (x, y) == self.ostatni_ruch:
                    aktualny_tekst = guzik.cget("text")
                    nowy_tekst = f"🤖{aktualny_tekst}" if aktualny_tekst else "🤖"
                    guzik.config(text=nowy_tekst, bg="#FFFACD")


if __name__ == "__main__":
    okno = tk.Tk()
    okno.title("SAPER AI - REPLAYER")

    saper_gui = MinyGUI(okno)

    okno.mainloop()