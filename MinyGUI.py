import time
import tkinter as tk
import random
import Miny


class MinyGUI:
    def __init__(self, env, okno):
        self.okno = okno
        self.env = env
        self.guziki = {}
        self.kolory = {
            1: 'blue',
            2: 'green',
            3: 'red',
            4: 'purple',
            5: 'pink',
            6: 'maroon',
            7: 'gray',
            8: 'turquoise'
        }

        # plansaa gry
        self.plansza_frame = tk.Frame(self.okno)
        self.plansza_frame.pack()

        # historia
        self.opcje = tk.Frame(self.okno)
        self.opcje.pack(pady=10)
        self.historia_ruchow = []
        self.index_historii = 0

        self.rysujOpcje()
        self.stworzPlansze()
        self.rysujPlansze()

    def rysujOpcje(self):
        self.guzik_wczytania = tk.Button(self.opcje, text="Wgraj", command=self.wczytajHistorie)
        self.guzik_wczytania.pack(side=tk.LEFT, padx=5)

        self.guzik_cofnij = tk.Button(self.opcje, text="⬅",  state=tk.DISABLED)
        self.guzik_cofnij.pack(side=tk.LEFT, padx=5)

        self.guzik_dalej = tk.Button(self.opcje, text="➡",state=tk.DISABLED)
        self.guzik_dalej.pack(side=tk.LEFT, padx=5)

    def wczytajHistorie(self):
        print("d")
    def stworzPlansze(self):
        for y in range(self.env.wielkosc_planszy):
            for x in range(self.env.wielkosc_planszy):
                guzik = tk.Button(self.plansza_frame, width=3, height=1, font=('Arial', 14, 'bold'))
                guzik.grid(row=y, column=x)
                self.guziki[(x, y)] = guzik

    def rysujPlansze(self):
        for y in range(self.env.wielkosc_planszy):
            for x in range(self.env.wielkosc_planszy):
                guzik = self.guziki[(x, y)]

                if self.env.plansza_obserwowana[y][x] == Miny.Obserwowane.FLAGA:
                    guzik.config(text="🚩", fg="red", relief=tk.SUNKEN, bg="SystemButtonFace", state=tk.DISABLED)
                elif self.env.plansza_obserwowana[y][x] == Miny.Obserwowane.ZAKRYTE:
                    guzik.config(text="", relief=tk.RAISED, bg="gray", state=tk.NORMAL)
                elif self.env.plansza_obserwowana[y][x] == Miny.Obserwowane.NIC:
                    guzik.config(text="", relief=tk.RAISED, bg="SystemButtonFace", state=tk.DISABLED)
                else:
                    kolor = self.kolory.get(self.env.plansza_obserwowana[y][x].value, 'black')
                    guzik.config(text=str(self.env.plansza_obserwowana[y][x].value), fg=kolor, relief=tk.SUNKEN,
                                 bg="SystemButtonFace", state=tk.DISABLED)

    def krok_ai(self):
        print("d")

if __name__ == "__main__":
    miny = Miny.SaperEnv(10, 10)
    miny.reset(time.time(), True)

    okno = tk.Tk()
    okno.title("SAPER")
    okno.resizable(False, False)
    saper = MinyGUI(miny, okno)

    okno.mainloop()