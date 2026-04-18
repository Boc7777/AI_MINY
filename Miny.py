from enum import Enum
import random
import time
import json
import re
import numpy as np
import os

class Obserwowane(Enum):
    CYFRA_1 = 1
    CYFRA_2 = 2
    CYFRA_3 = 3
    CYFRA_4 = 4
    CYFRA_5 = 5
    CYFRA_6 = 6
    CYFRA_7 = 7
    CYFRA_8 = 8
    NIC = 0
    ZAKRYTE = -1
    FLAGA = -2

class Wewnetrzna(Enum):
    MINA = 1
    BRAK_MINY = 0

class Akcja(Enum):
    FLAGA = 0
    STRZAL = 1

class SaperEnv:

    def __init__(self, wielkosc_planszy, liczba_min):
        self.wielkosc_planszy = wielkosc_planszy
        self.liczba_min = liczba_min
        self.plansza_obserwowana = []
        self.plansza_ukryta = []

        self.czyKoniecGry = False
        self.czyWygranaGra = False

        self.czy_zapisywać = False
        self.aktualny_seed = None
        self.historia_ruchow = []

    def getCzyKoniecGry(self):
        return self.czyKoniecGry

    def WygenerujPlansze(self,move):
        self.plansza_ukryta = []
        self.plansza_obserwowana = []
        #--------------------------------------STAN POCZATKOWY PLANSZY
        for _ in range(self.wielkosc_planszy):
            wiersz_ukr = []
            wiersz_obs = []
            for _ in range(self.wielkosc_planszy):
                wiersz_ukr.append(Wewnetrzna.BRAK_MINY)
                wiersz_obs.append(Obserwowane.ZAKRYTE)
            self.plansza_ukryta.append(wiersz_ukr)
            self.plansza_obserwowana.append(wiersz_obs)
        #--------------------------------------ZAPELNIENIE MINAMI
        for i in range(self.liczba_min):
            miejsce_dla_miny_znalezione = False
            while(miejsce_dla_miny_znalezione == False):
                newX = random.randint(0,self.wielkosc_planszy-1)
                newY = random.randint(0,self.wielkosc_planszy-1)

                if(newX >= move[0]-1 and newX <= move[0]+1 and
                   newY >= move[1]-1 and newY <= move[1]+1):
                    continue

                if self.plansza_ukryta[newY][newX] == Wewnetrzna.MINA:
                    continue

                self.plansza_ukryta[newY][newX] = Wewnetrzna.MINA
                miejsce_dla_miny_znalezione = True

    def printUkryta(self):
        for y in range(self.wielkosc_planszy):
            print()
            for x in range(self.wielkosc_planszy):
                if(self.plansza_ukryta[y][x] == Wewnetrzna.MINA):
                    print(1,end=" ")
                else:
                    print(0,end=" ")

    def printObserwowana(self):
        for y in range(self.wielkosc_planszy):
            print()
            for x in range(self.wielkosc_planszy):

                if(self.plansza_obserwowana[y][x].value == -1):
                    print("#",end=" ")
                    continue
                if(self.plansza_obserwowana[y][x].value == -2):
                    print("F",end=" ")
                    continue

                print(self.plansza_obserwowana[y][x].value,end=" ")

    def reset(self,seed = None, zapis=False):


        # dla AI bedzie przekazywana plansza juz po pierwszym ruchu ktory i tak nie ma znaczenia
        if (seed != None):
            random.seed(seed)


        move = (random.randint(0,self.wielkosc_planszy-1),random.randint(0,self.wielkosc_planszy-1))

        # ---------------------------------ZAPIS DO PLIKU
        if (zapis):
            self.czy_zapisywać = True
            self.aktualny_seed = seed
        else:
            self.czy_zapisywać = False
            self.aktualny_seed = None
            self.historia_ruchow = []


        self.WygenerujPlansze(move)
        self.step(move,Akcja.STRZAL)
        self.czyKoniecGry = False
        self.czyWygranaGra = False

        return self.get_state()

    def zapis_ruchow(self,move):
        if(self.czy_zapisywać):
            self.historia_ruchow.append(move)

    def step(self,move,akcja):

        self.zapis_ruchow(move)

        if(akcja == Akcja.FLAGA):
            aktualne_pole = self.plansza_obserwowana[move[1]][move[0]]

            # --------------------------------------------POSTAWIENIE FLAGI
            if aktualne_pole == Obserwowane.ZAKRYTE:
                self.plansza_obserwowana[move[1]][move[0]] = Obserwowane.FLAGA
                if(self.plansza_ukryta[move[1]][move[0]] == Wewnetrzna.MINA):
                    return self.plansza_obserwowana,self.czyKoniecGry,0.1

            # --------------------------------------------ZDEJMOWANIE FLAGI
            elif aktualne_pole == Obserwowane.FLAGA:
                self.plansza_obserwowana[move[1]][move[0]] = Obserwowane.ZAKRYTE
                return self.plansza_obserwowana, self.czyKoniecGry, -0.1

        elif(akcja == Akcja.STRZAL):
            # -------------------------------------------------------------------PRZEGRANA
            if(self.plansza_ukryta[move[1]][move[0]] == Wewnetrzna.MINA):
                self.czyKoniecGry = True
                self.zapisDoJsona()
                return self.plansza_obserwowana,self.czyKoniecGry,0

            # -------------------------------------------------------------------STRZELANIE W FALGE (NIE LEGALNE)
            if (self.plansza_obserwowana[move[1]][move[0]] == Obserwowane.FLAGA):
                return self.plansza_obserwowana,self.czyKoniecGry,-0.1

            # -------------------------------------------------------------------ZWYKLY RUCH
            tab = [move]
            self.OdkrywanieKaskadowe(tab)
            self.SprawdzCzyWygrana()
            return self.plansza_obserwowana,self.czyKoniecGry,0

    def OdkrywanieKaskadowe(self,tab):
        for i in tab:

            if self.plansza_obserwowana[i[1]][i[0]] != Obserwowane.ZAKRYTE:
                continue

            leftTopX = i[0]-1
            leftTopY = i[1]-1

            iloscMinWSasiedztwie = 0
            tabCzystych = []
            # SPRAWDZANIE SASIEDZTWA
            for y in range(3):
                for x in range(3):
                    if(y==1 and x==1):
                        continue

                    sprawdzanyX = leftTopX + x
                    sprawdzanyY = leftTopY + y

                    newMove = (sprawdzanyX,sprawdzanyY)

                    if(sprawdzanyX > self.wielkosc_planszy-1 or sprawdzanyY > self.wielkosc_planszy-1
                       or sprawdzanyX < 0 or sprawdzanyY < 0):
                        continue

                    if (self.plansza_ukryta[sprawdzanyY][sprawdzanyX] == Wewnetrzna.MINA):
                        iloscMinWSasiedztwie += 1
                        continue


                    if (self.plansza_obserwowana[sprawdzanyY][sprawdzanyX] != Obserwowane.ZAKRYTE):
                        continue
                    tabCzystych.append(newMove)

            if(iloscMinWSasiedztwie == 0):
                self.plansza_obserwowana[i[1]][i[0]] = Obserwowane.NIC
                self.OdkrywanieKaskadowe(tabCzystych)
            else:
                self.plansza_obserwowana[i[1]][i[0]] = Obserwowane(iloscMinWSasiedztwie)

    def SprawdzCzyWygrana(self):
        licznik = 0
        for y in range(self.wielkosc_planszy):
            for x in range(self.wielkosc_planszy):
                if(self.plansza_obserwowana[y][x] == Obserwowane.ZAKRYTE):
                    licznik += 1

        # ---------------------------------------------------WYGRANA
        if(licznik == self.liczba_min):
            self.czyWygranaGra = True
            self.czyKoniecGry = True
            self.zapisDoJsona()
            return True
        return False

    def zapisDoJsona(self):
        if not self.czy_zapisywać:
            return

        dane_do_zapisu = {
            "seed": self.aktualny_seed,
            "wymiar": self.wielkosc_planszy,
            "liczba_min": self.liczba_min,
            "wygrana": self.czyWygranaGra,
            "ruchy": self.historia_ruchow
        }

        folder = "zapisy"
        nazwa_pliku = f"powtorka_{int(self.aktualny_seed)}.json"

        sciezka_do_pliku = os.path.join(folder, nazwa_pliku)
        os.makedirs(folder, exist_ok=True)

        print(f"-------ZAPIS DO PLIKU: {sciezka_do_pliku}-------")
        json_string = json.dumps(dane_do_zapisu, indent=4)
        json_string = re.sub(r'\[\s+([-\d]+),\s+([-\d]+)\s+\]', r'[\1, \2]', json_string)

        # 4. Zapisujemy pod nową ścieżką
        with open(sciezka_do_pliku, "w") as plik:
            plik.write(json_string)

    def get_state(self):

        stan_surowy =[]
        for wierszy in self.plansza_obserwowana:
            for pole in wierszy:
                stan_surowy.append(pole.value)

        return np.array(stan_surowy, dtype=np.float32)

    def step_ai(self, akcja_id):
        rodzaj_akcji = Akcja.STRZAL

        y = akcja_id // self.wielkosc_planszy
        x = akcja_id % self.wielkosc_planszy
        move = (x, y)

        _, koniec_gry, _ = self.step(move, rodzaj_akcji)
        stan_dla_ai = self.get_state()

        nagroda = 0.0
        if koniec_gry:
            if self.czyWygranaGra:
                nagroda = 1.0
            else:
                nagroda = -1.0

        return stan_dla_ai, nagroda, koniec_gry




