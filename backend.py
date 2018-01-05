import os

from flask import (Flask,
                   jsonify,
                   abort,
                   Response, stream_with_context)
from flask_restful import Api, Resource

from flask_heroku import Heroku
from services.mi import video_to_summary
from services.tools import S3Helper
from services.gfycat import GfyClient

app = Flask(__name__)
api = Api(app)
app = Heroku(app).app
app.config.from_object('config')

s3 = S3Helper(app.config)
gfy_client = GfyClient(app.config)

class Transform(Resource):

    def get(self,
            s3_folder: str,
            s3_file: str,
            min_scene_secs: int,
            max_scenes: int):
        s3_key = os.path.join(s3_folder, s3_file)
        print('transform', s3_key)
        vid_filename = s3.download(s3_key)
        if vid_filename:
            process = video_to_summary(file_path=vid_filename,
                                       gfy_client=gfy_client,
                                       min_scene_secs=int(min_scene_secs),
                                       max_scenes=int(max_scenes))
            return Response(stream_with_context(process))
        else:
            abort(404)

api.add_resource(Transform,
                 ('/video/<string:s3_folder>'
                  '/<string:s3_file>'
                  '/<int:min_scene_secs>'
                  '/<int:max_scenes>'))

if __name__ == '__main__':
    app.run(debug=True)
