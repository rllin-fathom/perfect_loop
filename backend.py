
import os

from flask import (Flask,
                   jsonify,
                   abort)

from flask_heroku import Heroku
from services.mi import video_to_summary
from services.tools import S3Helper
from services.gfycat import GfyClient

app = Flask(__name__)
app = Heroku(app).app
app.config.from_object('config')

s3 = S3Helper(app.config)
gfy_client = GfyClient(app.config)

@app.route('/video/<s3_folder>/<s3_file>/<duration>',
           methods=['GET'])
def transform(s3_folder: str,
              s3_file: str,
              duration: float):
    s3_key = os.path.join(s3_folder, s3_file)
    print('transform', s3_key)

    vid_filename = s3.download(s3_key)

    if vid_filename:
        return jsonify(paths_to_gifs=video_to_summary(file_path=vid_filename,
                                                      gfy_client=gfy_client,
                                                      duration=duration))
    else:
        abort(404)

if __name__ == '__main__':
    app.run()
