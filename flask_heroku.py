import os

class Heroku(object):
    """Heroku configurations for flask."""

    def __init__(self, app) -> None:
        self.app = app
        if self.app is not None:
            self.assign_configs()

    def assign_configs(self) -> None:
        if 'HEROKU_API_KEY' in os.environ:
            import heroku3
            heroku_conn = heroku3.from_key(os.environ.get('HEROKU_API_KEY'))
            config = heroku_conn.app('cummary').config().to_dict()
        else:
            config = {k: v for k, v in os.environ.items()
                      if 'HEROKU_' in k}

        for key, value in config.items():
            self.app.config.setdefault(key.lstrip('HEROKU_'), value)

