import random
import time

import numpy as np

import Miny
from Agent import DQNAgent
import matplotlib.pyplot as plt


def run_experiment(episodes=1000,wczytaj_model=False):
    env = Miny.SaperEnv(wielkosc_planszy=6, liczba_min=6)
    agent = DQNAgent(board_size=6)
    batch_size = 32
    history_wins = []

    if wczytaj_model:
        agent.load_model("moj_saper_v1.pth")
        agent.epsilon = 0.3

    for e in range(episodes):
        # Używamy numeru epizodu jako seeda dla powtarzalności
        los = e*random.randint(0,999999999999)
        state = env.reset(seed= (los - (los%100000))+e, zapis=(e % 250 == 0))
        done = False

        while not done:
            action = agent.get_action(state)
            next_state, reward, done = env.step_ai(action)

            # Dodatkowa kara za powtarzanie ruchów (klikanie w to samo)
            if np.array_equal(state, next_state) and not done:
                reward = -0.5

            agent.remember(state, action, reward, next_state, done)
            state = next_state

            if done:
                print(
                    f"Epizod: {e}/{episodes}, Wynik: {'Wygrana' if env.czyWygranaGra else 'Bomba'}, Epsilon: {agent.epsilon:.2f}")
                history_wins.append(1 if env.czyWygranaGra else 0)

        if len(agent.memory) > batch_size:
            agent.train(batch_size)

    agent.save_model("moj_saper_v1.pth")
    return history_wins


# --- URUCHOMIENIE BADANIA ---
print("Trenowanie Agenta 'Od zera'...")
wins_normal = run_experiment(episodes=2000, wczytaj_model=False)


# Wykres wygranych (średnia krocząca)
def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w


plt.plot(moving_average(wins_normal, 100), label="Od zera")
plt.legend()
plt.title("Porównanie skuteczności agentów")
plt.show()


