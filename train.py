import random
import time

import numpy as np
import torch
from torch.optim.lr_scheduler import StepLR

import Miny
from Agent import DDQNAgent
import matplotlib.pyplot as plt


def run_experiment(episodes=1000,wczytaj_model=False):
    env = Miny.SaperEnv(wielkosc_planszy=6, liczba_min=3)
    agent = DDQNAgent(board_size=6)

    scheduler = StepLR(agent.optimizer, step_size=5000, gamma=0.5)
    batch_size = 128
    use_rules = False
    history_wins = []

    if wczytaj_model:
        agent.load_model("moj_saper_v1.pth")
        agent.epsilon = 0.3

    for e in range(episodes):
        los = e*random.randint(0,999999999999)
        state = env.reset(seed= (los - (los%100000))+e, zapis=(e % 250 == 0))
        done = False
        kroki = 0
        while not done:
            kroki += 1
            q_main, q_target = agent.get_q_values(state)

            action, is_random = agent.get_action(state,use_rules)

            next_state, reward, done = env.step_ai(action, q_values=(q_main, q_target),czy_losowy=is_random)

            if np.array_equal(state, next_state) and not done:
                reward = -0.5

            agent.remember(state, action, reward, next_state, done)
            state = next_state

            if done:
                if(e % 100 == 0):
                    print(
                        f"Epizod: {e}/{episodes}, Wynik: {'Wygrana' if env.czyWygranaGra else 'Bomba'}, Epsilon: {agent.epsilon:.2f}")
                history_wins.append(1 if env.czyWygranaGra else 0)

            if len(agent.memory) > batch_size and kroki % 1 == 0:
                agent.train(batch_size)
                agent.soft_update_target_model()

        scheduler.step()


    agent.save_model("moj_saper_v1.pth")
    return history_wins



print("Trenowanie Agenta 'Od zera'...")
wins_normal = run_experiment(episodes=20000, wczytaj_model=False)

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w


plt.plot(moving_average(wins_normal, 1000), label="Od zera")
plt.legend()
plt.title("Porównanie skuteczności agentów")
plt.show()


