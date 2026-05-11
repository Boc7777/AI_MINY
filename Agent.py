import os

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque


# 1. Architektura sieci neuronowej (Mózg Agenta)
class SaperNet(nn.Module):
    def __init__(self, input_size, output_size):
        super(SaperNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 256),  # Z 128 na 256
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 128),  # Dodatkowa warstwa zwężająca
            nn.ReLU(),
            nn.Linear(128, output_size)
        )

    def forward(self, x):
        return self.net(x)


# 2. Klasa Agenta DQN (Tabula Rasa)
class DQNAgent:
    def __init__(self, board_size):
        self.state_size = board_size * board_size
        self.action_size = board_size * board_size

        # Pamięć doświadczeń (Replay Buffer)
        self.memory = deque(maxlen=20000)

        # Hiperparametry uczenia
        self.gamma = 0.95  # Współczynnik dyskontowania
        self.epsilon = 1.0  # Początkowa szansa na ruch losowy (100%)
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995
        self.learning_rate = 0.00025

        self.model = SaperNet(self.state_size, self.action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def get_action(self, state):
        # 0. IDENTYFIKACJA DOZWOLONYCH RUCHÓW
        # Szukamy indeksów pól, których wartość to -1 (czyli Obserwowane.ZAKRYTE)
        valid_actions = [i for i, val in enumerate(state) if val < 0]

        # Zabezpieczenie: jeśli nie ma żadnych wolnych pól, wybierz cokolwiek (nie powinno się zdarzyć)
        if not valid_actions:
            return random.randrange(self.action_size)

        # 1. RZUT MONETĄ (Eksploracja)
        # Wybieramy losowo TYLKO z listy valid_actions
        if np.random.rand() <= self.epsilon:
            return random.choice(valid_actions)

        # 2. PYTANIE DO SIECI (Eksploatacja)
        state_t = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            act_values = self.model(state_t).numpy()[0] # Pobieramy wyniki jako tablicę numpy

        # --- MASKOWANIE AKCJI ---
        # Tworzymy tablicę wypełnioną bardzo małą liczbą (minus nieskończoność)
        masked_q_values = np.full(self.action_size, -np.inf)

        # Przepisujemy wartości Q tylko dla dozwolonych pól
        for i in valid_actions:
            masked_q_values[i] = act_values[i]

        # argmax wybierze teraz najlepsze pole spośród TYLKO tych zakrytych
        return int(np.argmax(masked_q_values))

    def remember(self, state, action, reward, next_state, done):
        """Zapisanie przeżycia do pamięci."""
        self.memory.append((state, action, reward, next_state, done))

    def train(self, batch_size):
        """Proces nauki na podstawie zebranych doświadczeń."""
        if len(self.memory) < batch_size:
            return

        # Losujemy paczkę wspomnień
        minibatch = random.sample(self.memory, batch_size)

        for state, action, reward, next_state, done in minibatch:
            state_t = torch.FloatTensor(state)
            next_state_t = torch.FloatTensor(next_state)

            # Obliczanie docelowej wartości Q (Target)
            target = reward
            if not done:
                # Używamy równania Bellmana: Q(s,a) = r + gamma * max(Q(s',a'))
                target = reward + self.gamma * torch.max(self.model(next_state_t)).item()

            # Pobieramy obecne przewidywania sieci
            target_f = self.model(state_t)

            # Aktualizujemy wartość tylko dla akcji, którą faktycznie wykonaliśmy
            with torch.no_grad():
                target_new = target_f.clone()
            target_new[action] = target

            # Krok optymalizacji sieci
            self.optimizer.zero_grad()
            loss = self.criterion(target_f, target_new)
            loss.backward()
            self.optimizer.step()

        # Stopniowe zmniejszanie losowości (agent staje się pewniejszy siebie)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, filename="saper_model.pth"):
        """Zapisuje wagi sieci do pliku."""
        torch.save(self.model.state_dict(), filename)
        print(f"Model zapisany jako {filename}")

    def load_model(self, filename="saper_model.pth"):
        """Wczytuje wagi sieci z pliku."""
        if os.path.exists(filename):
            self.model.load_state_dict(torch.load(filename))
            self.model.eval()  # Ustawia model w tryb oceny
            print(f"Model {filename} został wczytany!")
        else:
            print("Nie znaleziono pliku modelu, zaczynam naukę od zera.")