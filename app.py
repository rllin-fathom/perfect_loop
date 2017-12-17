"""Serves frontend"""
import os
from pathlib import PurePath
import tempfile
from typing import Dict

from flask import (Flask, request,
                   render_template, flash,
                   send_file, abort, Response,
                   url_for, jsonify)
from flask_wtf import Form
from flask_wtf.file import FileField
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
import requests
from werkzeug import secure_filename, formparser

from celery_utils import make_celery
from flask_heroku import Heroku
from services.tools import S3Helper

template_dir = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'templates')

app = Flask(__name__, template_folder=template_dir)
app = Heroku(app).app
app.config.from_object('config')

Bootstrap(app)
socketio = SocketIO(app)
                    #message_queue='redis://localhost:6379/0')

s3 = S3Helper(app.config)
celery = make_celery(app)

class UploadForm(Form):
    upload = FileField('Upload File')


@app.route('/', methods=['POST', 'GET'])
def index():
    form = UploadForm()
    task = None
    if form.validate_on_submit():
        print('submitted: ', form.upload.data)
        for progress, endpoint in s3.upload_stream(form.upload.data,
                                                   upload_dir='test'):
            print(progress, endpoint)
        #flash('{src} uploaded to S3 as {dst}'.format(
            #src=form.upload.data.filename, dst=endpoint))
        api_summarize.delay(endpoint)
        #flash(f'{result["webmUrl"]} to gfycat')

    return render_template('index.html', form=form)
    #status_url = url_for('taskstatus', task_id=task.id) if task else None
    #return render_template('index.html', form=form, status_url=status_url)
    #return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  #task_id=task.id)}

@celery.task()
def api_summarize(self, endpoint: str) -> Dict:
    end_path = os.path.join(*PurePath(endpoint).parts[-2:])
    socketio.emit('progress',
                  {'state': 'PENDING'},
                  namespace='/test')
    r = requests.get(f'https://urybbutmbh.execute-api.us-west-2.amazonaws.com/'
                     f'production/video/{end_path}',
                     headers={'x-api-key': 'aEyKJXgWXv65RRsAW5234Xsf3DuzMdF1oOhBI5Sa'})
    socketio.emit('progress',
                  {'state': 'SUCCESS', 'result': r.json()},
                  namespace='/test')


if __name__ == '__main__':
    #app.run()
    socketio.run(app)
