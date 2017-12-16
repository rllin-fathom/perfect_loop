import os

class Heroku(object):
    """Heroku configurations for flask."""

    def __init__(self, app=None):
        self.app = app
        if self.app is not None:
            self.assign_configs()
        return self.app

    def assign_configs(self) -> None:
        for key, value in os.environ.items():
            if 'HEROKU_' in key:
                self.app.config.setdefault(key.lstrip('HEROKU_'), value)
