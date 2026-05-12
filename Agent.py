import os

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque


class SaperNet(nn.Module):
    def __init__(self, board_size, output_size):
        super(SaperNet, self).__init__()
        self.board_size = board_size

        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU()
        )

        self.fc = nn.Sequential(
            nn.Linear(64 * board_size * board_size, 128),
            nn.ReLU(),
            nn.Linear(128, output_size)
        )

    def forward(self, x):
        x = x.view(-1, 1, self.board_size, self.board_size)
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


class DDQNAgent:
    def __init__(self, board_size):
        self.state_size = board_size * board_size
        self.action_size = board_size * board_size

        #Replay Buffer
        self.memory = deque(maxlen=100000)


        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.025
        self.epsilon_decay = 0.9995
        self.learning_rate = 0.0001
        self.tau = 0.005

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = SaperNet(board_size, self.action_size).to(self.device)
        self.target_model = SaperNet(board_size, self.action_size).to(self.device)

        self.update_target_model()


        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()

    def soft_update_target_model(self):
        for target_param, local_param in zip(self.target_model.parameters(), self.model.parameters()):
            target_param.data.copy_(self.tau * local_param.data + (1.0 - self.tau) * target_param.data)

    def get_action(self, state):
        valid_actions = [i for i, val in enumerate(state) if val < 0]
        if not valid_actions:
            return random.randrange(self.action_size), True  #

        # RZUT MONETĄ (Eksploracja)
        if np.random.rand() <= self.epsilon:
            return random.choice(valid_actions), True  # Zwracamy True dla losowego

        # PYTANIE DO SIECI (Eksploatacja)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            act_values = self.model(state_t).cpu().numpy()[0]

        masked_q_values = np.full(self.action_size, -np.inf)
        for i in valid_actions:
            masked_q_values[i] = act_values[i]

        return int(np.argmax(masked_q_values)), False  # Zwracamy False dla AI




        # 2. PYTANIE DO SIECI (Eksploatacja)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            act_values = self.model(state_t).cpu().numpy()[0] # Pobieramy wyniki jako tablicę numpy

        # --- MASKOWANIE AKCJI ---
        # Tworzymy tablicę wypełnioną bardzo małą liczbą (minus nieskończoność)
        masked_q_values = np.full(self.action_size, -np.inf)

        # Przepisujemy wartości Q tylko dla dozwolonych pól
        for i in valid_actions:
            masked_q_values[i] = act_values[i]

        # argmax wybierze teraz najlepsze pole spośród TYLKO tych zakrytych
        return int(np.argmax(masked_q_values))

    def get_q_values(self, state):
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_main = self.model(state_t).cpu().numpy()[0]
            q_target = self.target_model(state_t).cpu().numpy()[0]
        return q_main, q_target

    def remember(self, state, action, reward, next_state, done):
        """Zapisanie przeżycia do pamięci."""
        self.memory.append((state, action, reward, next_state, done))

    def train(self, batch_size):
        """Proces nauki na podstawie zebranych doświadczeń."""
        if len(self.memory) < batch_size:
            return

        # Losujemy paczkę wspomnień
        minibatch = random.sample(self.memory, batch_size)

        # 1. WEKTORYZACJA: Tworzymy duże macierze zamiast pętli FOR
        states = torch.FloatTensor(np.array([m[0] for m in minibatch])).to(self.device)
        actions = torch.LongTensor([m[1] for m in minibatch]).to(self.device)
        rewards = torch.FloatTensor([m[2] for m in minibatch]).to(self.device)
        next_states = torch.FloatTensor(np.array([m[3] for m in minibatch])).to(self.device)
        dones = torch.BoolTensor([m[4] for m in minibatch]).to(self.device)

        # 2. OBLICZANIE TARGETÓW (Wszystkie 32 naraz!)
        # Używamy modelu do przewidzenia Q dla obecnych i przyszłych stanów
        curr_q_values = self.model(states)

        with torch.no_grad():

            next_actions = self.model(next_states).argmax(1).unsqueeze(1)
            next_q_values = self.target_model(next_states).gather(1, next_actions).squeeze(1)
            targets = rewards + (self.gamma * next_q_values * (~dones))

        # Przygotowujemy wynik do porównania
        target_f = curr_q_values.clone()
        # Podmieniamy tylko wartości dla podjętych akcji
        target_f.scatter_(1, actions.unsqueeze(1), targets.unsqueeze(1))

        # 3. JEDEN KROK OPTYMALIZACJI DLA CAŁEJ PACZKI
        self.optimizer.zero_grad()
        loss = self.criterion(curr_q_values, target_f)
        loss.backward()
        self.optimizer.step()

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