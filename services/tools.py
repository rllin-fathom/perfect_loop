
from functools import wraps
import tempfile
from typing import Iterator
from uuid import uuid4
import os


import boto3
from flask import current_app as app
from flask import request, abort
from werkzeug.utils import secure_filename


def get_resource(res_name, region, aws_key=None, aws_secret=None):
    try:
        return boto3.resource(res_name,
                             region,
                             aws_access_key_id=aws_key,
                             aws_secret_access_key=aws_secret)
    except ResourceNotExistsError:
        pass


class S3Helper(object):
    def __init__(self, config):
        self.region = config['AWS_REGION']
        self.aws_key = config['AWS_KEY']
        self.aws_secret = config['AWS_SECRET']
        self.bucket = config['S3_BUCKET']
        self.resource = get_resource('s3',
                                     self.region,
                                     aws_key=self.aws_key,
                                     aws_secret=self.aws_secret)


    def download(self, key):
        """
        Download the file from s3 given `bucket` and `key`.
        Returns
        -------
        str
            the filename of the downloaded file or None if the file was not found
        """
        temp_path = os.path.join(tempfile.gettempdir(), key)
        print('Downloading file from s3 at {} to {}'.format(key, temp_path))
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        self.resource.Bucket(
            self.bucket).download_file(
                key, temp_path)
        return temp_path

    def upload(self, source_filename, upload_dir = None):
        """ Uploads WTForm File Object to Amazon S3

            The default sets the access rights on the uploaded file to
            public-read.  It also generates a unique filename via
            the uuid4 function combined with the file extension from
            the source file.
        """
        source_extension = os.path.splitext(source_filename)[1]

        if not upload_dir:
            upload_dir = uuid4().hex

        s3_file_path = os.path.join(upload_dir,
                                    uuid4().hex + source_extension)

        with open(source_filename, 'rb') as f:
            self.resource.Bucket(
                self.bucket).upload_fileobj(
                    f,
                    s3_file_path,
                    ExtraArgs={'ACL': 'public-read'})

        return self._endpoint(s3_file_path)

    def upload_stream(self,
                      file_path: str,
                      upload_dir: str = None,
                      chunk_size: int = 5 * 1024 * 1024,
                      progress: bool = False) -> str:
        if not upload_dir:
            upload_dir = uuid4().hex

        s3_file_path = os.path.join(
            upload_dir,
            uuid4().hex
            + os.path.splitext(file_path)[1])

        bucket = self.resource.Object(self.bucket, s3_file_path)
        mp = bucket.initiate_multipart_upload(ACL='public-read')
        #'bucket-owner-full-control')

        parts_etag = {}
        chunk_idx = 1
        with open(file_path, 'rb') as stream:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break

                part = mp.Part(chunk_idx)
                result = part.upload(Body=chunk)
                parts_etag[str(chunk_idx)] = result['ETag']

                chunk_idx += 1
                yield chunk_idx - 1, self._endpoint(s3_file_path)

        mp.complete(
            MultipartUpload={
                'Parts': [{'ETag': parts_etag[str(idx)],
                           'PartNumber': idx}
                          for idx in range(1, chunk_idx)]})
        yield chunk_idx - 1, self._endpoint(s3_file_path)

    def _endpoint(self, file_path: str) -> str:
        return os.path.join('http://s3-{}.amazonaws.com'.format(self.region),
                            self.bucket,
                            file_path)


# The actual decorator function
def require_apikey(config):
    def wrap(view_function):
        @wraps(view_function)
        # the new, post-decoration function. Note *args and **kwargs here.
        def decorated_function(*args, **kwargs):
            if (request.args.get('x-api-key')
                    and request.args.get('x-api-key') == config['AWS_API_KEY']):
                return view_function(*args, **kwargs)
            else:
                abort(401)
        return decorated_function
    return wrap
