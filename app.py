"""Serves frontend"""
import os
import tempfile
from typing import Dict

from flask import (Flask, request,
                   render_template, flash,
                   send_file, abort, Response)
from flask_wtf import Form
from flask_wtf.file import FileField
from flask_bootstrap import Bootstrap
import requests
from werkzeug import secure_filename, formparser

from flask_heroku import Heroku
from services.tools import S3Helper

template_dir = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'templates')

app = Flask(__name__, template_folder=template_dir)
app = Heroku(app).app
app.config.from_object('config')

Bootstrap(app)

s3 = S3Helper(app.config)

class UploadForm(Form):
    upload = FileField('Upload File')


@app.route('/', methods=['POST', 'GET'])
def index():
    form = UploadForm()
    if form.validate_on_submit():
        for progress, endpoint in s3.upload_stream(form.upload.data,
                                                   upload_dir='test'):
            print(progress, endpoint)
        flash('{src} uploaded to S3 as {dst}'.format(
            src=form.upload.data.filename, dst=endpoint))
        result = api_summarize(endpoint)
        flash(result)
        flash(f'{result} to gfycat')
    return render_template('index.html', form=form)


def api_summarize(endpoint: str) -> Dict:
    end_path = os.path.join(*PurePath(endpoint).parts[-2:])
    r = requests.get(f'https://urybbutmbh.execute-api.us-west-2.amazonaws.com/'
                     f'production/video/{end_path}',
                     headers={'x-api-key': 'aEyKJXgWXv65RRsAW5234Xsf3DuzMdF1oOhBI5Sa'})
    print(r.json())
    return r.json()


if __name__ == '__main__':
    app.run()
