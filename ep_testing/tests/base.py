class BaseTest:

    def name(self):
        raise NotImplementedError('name() must be overridden by derived classes')

    def run(self, install_root: str, kwargs: dict):
        raise NotImplementedError('run() must be overridden by derived classes')

