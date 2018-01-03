import json
import os

class Heroku(object):
    """Heroku configurations for flask."""

    def __init__(self, app) -> None:
        self.app = app
        if self.app is not None:
            self.assign_configs()

    def assign_configs(self) -> None:
        local_keys = 'private_keys.json'
        remote_keys = '/etc/pki/tls/certs/private_keys.json'
        if os.isfile(local_keys):
            keys_path = local_keys
        elif os.isfile(remote_keys):
            keys_path = remote_keys

        with open(keys_path, 'r') as keys_f:
            config = json.load(keys_f)
        '''
        if 'HEROKU_API_KEY' in os.environ:
            print('Using credentials from heroku')
            import heroku3
            heroku_conn = heroku3.from_key(os.environ.get('HEROKU_API_KEY'))
            config = heroku_conn.app('cummary').config().to_dict()
        else:
            print('Using credentials from local environment')
            config = {k: v
                      for k, v in os.environ.items()
                      if 'HEROKU_' in k}
        '''
        for key, value in config.items():
            self.app.config.setdefault(key.lstrip('HEROKU_'), value)
        self.app.config.setdefault('SECRET_KEY', os.urandom(1))
