class StateMachine():
    """ Generic state machine
    """
    def __init__(self, *args, **kwargs):
        self.states = set()
        self.state = None

    def add_state(self, state):
        """ Add a new state to the state machine

            :param str state: Name of the state
        """
        self.states.add(state)

    def set_state(self, state):
        """ Change state of the state machine

            :param str state: Name of the new state
        """
        assert state in self.states, "Unknown State"
        self.state = state

    def get_state(self):
        """ Return state of state machine
        """
        return self.state
