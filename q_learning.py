import numpy as np

'''
    q-table: 2-dimensional array[2][2]
        1st dimension: states
            0: Exploration / Digging mode
            1: Exploitation / Honey mode
        2nd dimension: actions
            0: Stay in current state
            1: Change state
    
    reward: 1-dimensional array[2]
        0: Negative
        1: Positive
'''
class Q_Learning:
    def __init__(self, states, actions, parameters):
        self.states = states
        self.actions = actions
        self.reward = parameters['reward']
        self.alpha = parameters['alpha']
        self.gamma = parameters['gamma']
        self.eps = parameters['eps']
        self.chi = parameters['chi']
        self._q_table = np.zeros((states, actions))
        self.current_state = 0
        self.next_state = None
        self.chosen_action = None

    def _do_action(self):
        if self.chosen_action == 0:
            self.next_state = self.current_state
        else:
            self.next_state = (self.current_state + 1) % 2

    def update(self, result):
        current_value = self._q_table[self.current_state][self.chosen_action]
        reward = self.reward[result] if result else 0
        next_state_max = np.max(self._q_table[self.next_state])
        self._q_table[self.current_state][self.chosen_action] = (1 - self.alpha) * current_value + self.alpha * (
                    reward + self.gamma * next_state_max)
        self.current_state = self.next_state

    def choose_action(self):
        action_values = self._q_table[self.current_state]
        r = np.random.rand()
        # Random
        if r <= self.eps:
            self.chosen_action = np.random.randint(self.states)
        # Roulette wheel
        elif r <= self.eps + self.chi:
            current_point = 0
            selected_point = np.random.rand() * np.sum(action_values)
            for i in range(len(action_values)):
                current_point += action_values[i]
                if current_point >= selected_point:
                    self.chosen_action = i
                    break
        # Maximum value
        else:
            self.chosen_action = np.argmax(action_values)

        self._do_action()
