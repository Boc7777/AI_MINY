from enum import Enum
import random
import time

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

    def printUkryta(self):
        for y in range(self.wielkosc_planszy):
            print()
            for x in range(self.wielkosc_planszy):
                print(self.plansza_ukryta[y][x].value,end=" ")

    def printObserwowana(self):
        for y in range(self.wielkosc_planszy):
            print()
            for x in range(self.wielkosc_planszy):
                print(self.plansza_obserwowana[y][x].value,end=" ")

    def reset(self,seed = None):
        # dla AI bedzie przekazywana plansza juz po pierwszym ruchu ktory i tak nie ma znaczenia
        if (seed != None):
            random.seed(seed)

        move = (random.randint(0,self.wielkosc_planszy-1),random.randint(0,self.wielkosc_planszy-1))
        self.WygenerujPlansze(move)
        self.step(move,Akcja.STRZAL)
        self.czyKoniecGry = False

    def step(self,move,akcja):
        if(akcja == Akcja.FLAGA):
            self.plansza_obserwowana[move[1]][move[0]] = Obserwowane.FLAGA
            #------------EWENTUALNA NAGORDA ___DO_ZROBIENIA___
        elif(akcja == Akcja.STRZAL):

            if(self.plansza_ukryta[move[1]][move[0]] == Wewnetrzna.MINA):
                self.czyKoniecGry = True
                return self.plansza_obserwowana,self.czyKoniecGry #+NAGRODA

            tab = [move]
            self.OdkrywanieKaskadowe(tab)
            return self.plansza_obserwowana,self.czyKoniecGry #+NAGRODA

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


miny = SaperEnv(10,10)
while(True):
    input()
    miny.reset(time.time())
    miny.printObserwowana()

