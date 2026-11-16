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
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU()
        )

        self.fc = nn.Sequential(
            nn.Linear(256 * board_size * board_size, 256),
            nn.ReLU(),
            nn.Linear(256, output_size)
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
        self.board_size = board_size
        #Replay Buffer
        self.memory = deque(maxlen=100000)


        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.025
        self.epsilon_decay = 0.9996
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

    def get_action(self, state, use_rules=False):
        # 1. PRÓBA UŻYCIA ZASAD LOGICZNYCH
        if use_rules:
            board_2d = state.reshape(self.board_size, self.board_size)
            safe_actions = self.check_basic_rules(board_2d)

            if safe_actions:
                return safe_actions[0], False

        # 2. DECYZJA SIECI NEURONOWEJ
        valid_actions = [i for i, val in enumerate(state) if val < 0]

        if not valid_actions:
            return 0, False

        #(Ruch losowy)
        if np.random.rand() <= self.epsilon:
            # Ruch czysto losowy -> True
            return random.choice(valid_actions), True

        #(CNN - Ruch zaplanowany)
        else:
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)

            with torch.no_grad():
                q_values = self.model(state_t).squeeze(0).cpu().numpy()

            masked_q_values = np.full(self.board_size * self.board_size, -np.inf)
            for act in valid_actions:
                masked_q_values[act] = q_values[act]

            return int(np.argmax(masked_q_values)), False

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


        states = torch.FloatTensor(np.array([m[0] for m in minibatch])).to(self.device)
        actions = torch.LongTensor([m[1] for m in minibatch]).to(self.device)
        rewards = torch.FloatTensor([m[2] for m in minibatch]).to(self.device)
        next_states = torch.FloatTensor(np.array([m[3] for m in minibatch])).to(self.device)
        dones = torch.BoolTensor([m[4] for m in minibatch]).to(self.device)

        curr_q_values = self.model(states)

        with torch.no_grad():

            next_actions = self.model(next_states).argmax(1).unsqueeze(1)
            next_q_values = self.target_model(next_states).gather(1, next_actions).squeeze(1)
            targets = rewards + (self.gamma * next_q_values * (~dones))


        target_f = curr_q_values.clone()

        target_f.scatter_(1, actions.unsqueeze(1), targets.unsqueeze(1))


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
            self.model.eval()
            print(f"Model {filename} został wczytany!")
        else:
            print("Nie znaleziono pliku modelu, zaczynam naukę od zera.")

    def check_basic_rules(self, board_2d):
        """
        Skanuje planszę i zwraca listę indeksów pól (0-24 lub 0-35),
        które na 100% są bezpieczne do kliknięcia na podstawie podstawowej logiki.
        """
        size = self.board_size
        guaranteed_safe = set()
        mines_found = set()

        # Pomocnicza funkcja do pobierania sąsiadów
        def get_neighbors(r, c):
            return [(r + dr, c + dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1]
                    if (dr != 0 or dc != 0) and 0 <= r + dr < size and 0 <= c + dc < size]

        # Przebieg 1: Szukamy pewnych min (żeby wiedzieć, gdzie są flagi)
        for r in range(size):
            for c in range(size):
                val = board_2d[r][c]
                if val > 0:  # Jeśli to odkryta cyfra (zakładamy wartości > 0 dla cyfr)
                    # W Twoim kodzie cyfry mogą być przeskalowane (np. cyfra/8.0)
                    # Musisz pomnożyć przez 8.0, żeby odzyskać prawdziwą cyfrę!
                    true_val = round(val * 8.0)

                    neighbors = get_neighbors(r, c)
                    hidden = [n for n in neighbors if board_2d[n[0]][n[1]] == -0.1]  # Zakryte

                    if len(hidden) == true_val:
                        for h in hidden:
                            mines_found.add(h[0] * size + h[1])  # Zapisujemy płaski indeks

        # Przebieg 2: Szukamy pewnych bezpiecznych pól
        for r in range(size):
            for c in range(size):
                val = board_2d[r][c]
                if val > 0:
                    true_val = round(val * 8.0)
                    neighbors = get_neighbors(r, c)

                    hidden = [n for n in neighbors if board_2d[n[0]][n[1]] == -0.1]
                    hidden_indices = [n[0] * size + n[1] for n in hidden]

                    # Liczymy ile z tych ukrytych to już "pewne miny"
                    flags_around = [idx for idx in hidden_indices if idx in mines_found]

                    # Jeśli znaleźliśmy już tyle min, ile mówi cyfra, reszta ukrytych jest bezpieczna!
                    if len(flags_around) == true_val:
                        safe_ones = [idx for idx in hidden_indices if idx not in mines_found]
                        for s in safe_ones:
                            guaranteed_safe.add(s)

        return list(guaranteed_safe)