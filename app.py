"""Serves frontend"""
import os
import tempfile

from flask import Flask, request, render_template, flash, send_file, abort, Response
from flask_wtf import Form
from flask_wtf.file import FileField
from flask_bootstrap import Bootstrap
from werkzeug import secure_filename, formparser

from services.tools import S3Helper

template_dir = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'templates')

app = Flask(__name__, template_folder=template_dir)
app.config.from_object('config')
app.debug = True

Bootstrap(app)

s3 = S3Helper(app.config)

class UploadForm(Form):
    upload = FileField('Upload File')


@app.route('/', methods=['POST', 'GET'])
def index():
    form = UploadForm()
    if form.validate_on_submit():
        source_filename = secure_filename(form.upload.data.filename)
        for progress, endpoint in s3.upload_stream(source_filename,
                                                   upload_dir='test'):
            print(progress, endpoint)
        flash('{src} uploaded to S3 as {dst}'.format(
            src=form.upload.data.filename, dst=endpoint))
    return render_template('index.html', form=form)


if __name__ == '__main__':
    app.run()
