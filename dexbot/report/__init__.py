
"""
A framework for reporting
an an email based reporter
"""

class BaseReporter:
    """Abstract base class for reporter plugins
    """

    def ontick(self):
        """Called for every tick
        """
        pass

    def shutdown(self):
        """Disconnect the reporter if required"""
        pass
