import requests
import time

auth_url = 'https://api.gfycat.com/v1/oauth/token'
upload_url = 'https://api.gfycat.com/v1/gfycats'
root_status_url = 'https://api.gfycat.com/v1/gfycats/fetch/status/'
root_check_link_url = 'http://gfycat.com/cajax/get/'
root_update_gfy_url = 'https://api.gfycat.com/v1/me/gfycats/'
root_md5_url = 'http://gfycat.com/cajax/checkUrl/'


class GfyClient(object):
    def __init__(self, config):
        self.client_id = config.get('GFYCAT_ID')
        self.client_secret = config.get('GFYCAT_KEY')
        self.username = config.get('GFYCAT_USERNAME')
        self.password = config.get('GFYCAT_PW')
        self.refresh_token = None
        self.access_token = None

        if self.client_id is None:
            raise TypeError('client id required')
        if self.client_secret is None:
            raise TypeError('client secret is required')

        self.oauth = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }
        self.authorize_me()

    def authorize_me(self):
        try:
            r = requests.post(auth_url, json=self.oauth)
            self.access_token = r.json()['access_token']
            self.refresh_token = r.json()['refresh_token']
            print('retrieved access token')
        except requests.exceptions.RequestException as e:
            print('could not get authenticate')

    def upload_from_file(self, file_path, **kwargs):
        title = kwargs.get('title', None)
        start  = kwargs.get('start', None)
        duration  = kwargs.get('duration', None)
        tags = kwargs.get('tags', None)

        if title != None:
            upload_dict.update({'title':title})
        if tags != None:
            upload_dict.update({'tags':tags})

        header = {'Authorization': self.access_token,
                  'Content-Type': 'application/json'}

        try:
            r = requests.post('https://api.gfycat.com/v1/gfycats',
                              headers=header)
            key = r.json()['gfyname']
        except requests.exceptions.RequestException as e:
            print('could not get key')
            print('exception: {}'.format(e))
            return

        with open(file_path, 'rb') as f:
            try:
                r = requests.post('https://filedrop.gfycat.com',
                                  files={'file': f},
                                  data={'key': key})
            except requests.exceptions.RequestException as e:
                print('could not upload file')

        status_url = root_status_url + key
        time.sleep(2)
        while True:
            state = self.check_status(key)
            if state == 'complete':
                return self.current_response
            elif state == 'encoding':
                time.sleep(1)
                continue

    def check_status(self, key):
        status_url = root_status_url + key
        print('checking', key)
        try:
            r = requests.get(status_url)
            self.current_response = r.json()
            task_state = self.current_response['task']

            if task_state == "encoding":
                print('encoding')
            elif task_state == 'complete':
                print('gfycat complete! Gfyname: {}'.format(key))
            elif task_state == 'NotFoundo':
                print('gfycat not found, something went wrong')
            elif task_state == 'error':
                print('Something went wrong uploading url')
            else:
                print('unknwn status')
                task_state = 'error'
        except requests.exceptions.RequestException as e:
            print('could not fetch url')
            task_state = 'error'
        return task_state

    def delete_gfy(self, key):
        # need gfyname, not link
        url = root_update_gfy_url + key
        header = {'Authorization': self.access_token,
                  'Content-Type': 'application/json'}
        try:
            r = requests.delete(url, headers=header)
            # no response if sucessful, so if I get something back its an error
            if r.text:
                return r.json()['errorMessage']['description']
            else:
                print("Deleted Gfy")
        except requests.exceptions.RequestException as e:
            print('error')
