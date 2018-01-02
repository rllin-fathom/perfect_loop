import os

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['mp4'])

SECRET_KEY = os.urandom(32)
DEBUG = True
PORT = 5000
