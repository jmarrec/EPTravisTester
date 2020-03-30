class BaseTest:

    def __init__(self):
        self.verbose = False

    def name(self):
        raise NotImplementedError('name() must be overridden by derived classes')

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        raise NotImplementedError('run() must be overridden by derived classes')
