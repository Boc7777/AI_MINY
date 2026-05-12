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

    def zapis_ruchow(self, move, akcja, q_values=None, czy_losowy=False):
        if self.czy_zapisywać:
            # Jeśli q_values to lista/krotka dwóch tablic, zamień każdą na listę
            serialized_q = None
            if q_values is not None:
                # Zapisujemy jako listę dwóch list: [lista_main, lista_target]
                serialized_q = [q.tolist() for q in q_values]

            self.historia_ruchow.append({
                "coords": [int(move[0]), int(move[1])],
                "akcja": akcja.value,
                "q_values": serialized_q,
                "losowy": czy_losowy
            })

    def step(self,move,akcja, q_values=None, czy_losowy=False):

        self.zapis_ruchow(move, akcja, q_values=q_values, czy_losowy=czy_losowy)

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

            # -------------------------------------------------------------------STRZELANIE W FALGE (NIE LEGALNE)
            if (self.plansza_obserwowana[move[1]][move[0]] == Obserwowane.FLAGA):
                return self.plansza_obserwowana, self.czyKoniecGry, -0.1

            # -------------------------------------------------------------------PRZEGRANA
            if(self.plansza_ukryta[move[1]][move[0]] == Wewnetrzna.MINA):
                self.czyKoniecGry = True
                self.zapisDoJsona()
                return self.plansza_obserwowana,self.czyKoniecGry,0

            # -------------------------------------------------------------------ZWYKLY RUCH
            tab = [move]
            self.OdkrywanieKaskadowe(tab)
            self.SprawdzCzyWygrana()
            return self.plansza_obserwowana,self.czyKoniecGry,0.4

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
        nazwa_pliku = f"powtorka_{len(self.historia_ruchow)}_{int(self.aktualny_seed)}.json"

        sciezka_do_pliku = os.path.join(folder, nazwa_pliku)
        os.makedirs(folder, exist_ok=True)

        print(f"-------ZAPIS DO PLIKU: {sciezka_do_pliku}-------")
        json_string = json.dumps(dane_do_zapisu, indent=4)
        json_string = re.sub(
            r'\[\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\]',
            r'[\1, \2, \3]',
            json_string
        )

        # 4. Zapisujemy pod nową ścieżką
        with open(sciezka_do_pliku, "w") as plik:
            plik.write(json_string)

    def get_state(self):

        stan_surowy =[]
        for wierszy in self.plansza_obserwowana:
            for pole in wierszy:
                val = pole.value
                if val == -1:
                    stan_surowy.append(-0.1)
                elif val == -2:
                    stan_surowy.append(-0.2)
                else:
                    stan_surowy.append(val / 8.0)

        return np.array(stan_surowy, dtype=np.float32)

    def step_ai(self, akcja_id, q_values=None, czy_losowy=False):
        rodzaj_akcji = Akcja.STRZAL

        y = akcja_id // self.wielkosc_planszy
        x = akcja_id % self.wielkosc_planszy
        move = (x, y)


        _, koniec_gry, nagr = self.step(move, rodzaj_akcji, q_values=q_values, czy_losowy=czy_losowy)
        stan_dla_ai = self.get_state()

        nagroda = nagr
        if koniec_gry:
            if self.czyWygranaGra:
                nagroda = 20.0
            else:
                nagroda = -15.0

        return stan_dla_ai, nagroda, koniec_gry


# miny = SaperEnv(10,10)
# miny.reset(13,True)
# while(True):
#     miny.printObserwowana()
#     czyZapis = input("czy zapisać? ")
#
#     if(czyZapis == "1"):
#         miny.zapisDoJsona()
#
#     x = input("Podaj x")
#     y = input("Podaj y")
#     akcja = input("Podaj akcja")
#     if(akcja == "1"):
#         akcja = Akcja.STRZAL
#     else:
#         akcja = Akcja.FLAGA
#     miny.step((int(x),int(y)),akcja)






