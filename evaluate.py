# evaluate.py
import torch
import numpy as np
from Agent import DDQNAgent
from Miny import SaperEnv  # Twoje środowisko
import Miny


def uruchom_testy(sciezka_do_modelu, uzyj_zasad=False, liczba_gier=1000):
    env = SaperEnv(wielkosc_planszy=6, liczba_min=4)
    agent = DDQNAgent(board_size=6)

    # 1. Ładujemy wyuczony mózg i zamrażamy go
    agent.model.load_state_dict(torch.load(sciezka_do_modelu))
    agent.model.eval()
    agent.epsilon = 0.0  # ZERO LOSOWOŚCI

    wygrane = 0
    ruch_w_grze = []

    # Stałe plansze zapewniają identyczne warunki dla każdego wywołania
    for gra in range(liczba_gier):
        state = env.reset(seed=gra*9999999999999)  # Stały seed gwarantuje te same plansze dla każdego modelu!
        done = False
        kroki = 0

        while not done:
            # get_action z Twoją flagą use_rules
            action, is_random = agent.get_action(state, use_rules=uzyj_zasad)

            # --- POPRAWKA: Używamy step_ai zamiast step i odbieramy 3 wartości ---
            state, reward, done = env.step_ai(action)
            kroki += 1

            if done:
                # --- POPRAWKA: Sprawdzamy stan wygranej bezpośrednio z obiektu env ---
                if env.czyWygranaGra:
                    wygrane += 1
                ruch_w_grze.append(kroki)

    print(f"--- WYNIKI DLA: {sciezka_do_modelu} (Zasady: {uzyj_zasad}) ---")
    print(f"Skuteczność: {wygrane / liczba_gier * 100:.2f}%")
    print(f"Średnia liczba kroków w grze: {np.mean(ruch_w_grze):.2f}")


# Wywołanie:
uruchom_testy("modele/saper_6x6x4_sieć64_bez_zasad.pth", uzyj_zasad=False)
uruchom_testy("modele/saper_6x6x4_sieć64_bez_zasad.pth", uzyj_zasad=True)