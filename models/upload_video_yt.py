import os
import pathlib
import random
import subprocess
import base64

from odoo import fields, models, api
from odoo.exceptions import ValidationError

from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

YOUTUBE_API_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]


class UploadVideoYt(models.Model):
    _name = 'upload.video.yt'
    _description = 'Upload video to youtube'

    categoryId = fields.Char(string='Category ID', required=True)
    title = fields.Char(string='Title', required=True)
    description = fields.Char(string='Description', required=True)
    tags = fields.Char(string='Tags', required=True)
    publishAt = fields.Datetime(string='publishAt', required=True)
    isPublish = fields.Boolean(string='Is Publish', default=False, readonly=True)
    channel = fields.Many2one('google.access.token', string='Youtube Channel', required=True)
    video_file = fields.Binary('Video file')

    @staticmethod
    def overwrite_input_file(path, data):
        file = open(path, 'wb')
        file.write((base64.b64decode(data)))
        file.close()

    def get_mp4_file(self):
        input_file = f'{pathlib.Path(__file__).parent.parent}/static/video/video.bin'
        self.overwrite_input_file(input_file, self.video_file)

        output_file = f'{pathlib.Path(__file__).parent.parent}/static/video/{random.randint(10000, 99999)}.mp4'

        command = f"ffmpeg -i {input_file} {output_file}"
        subprocess.call(command, shell=True)

        return output_file

    def upload(self):
        if self.isPublish:
            raise ValidationError("This video already upload to youtube!")
        else:
            tags = self.tags.split(" ")
            tags = [word for word in tags if word]

            body = {
                'snippet': {
                    'categoryId': self.categoryId,
                    'title': self.title,
                    'description': self.description,
                    'tags': tags,
                },
                'status': {
                    'privacyStatus': 'private',
                    'publishAt': self.publishAt.isoformat(),
                },
            }

            client_id = self.env['ir.config_parameter'].sudo().get_param('tiktok_post.google_client_id')
            client_secret = self.env['ir.config_parameter'].sudo().get_param('tiktok_post.google_client_secret')

            youtube = self.build_youtube_obj(self.channel, client_id, client_secret)

            file_path = self.get_mp4_file()
            print(f'Created file at {file_path}')

            res = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True))

            print('Uploading file...')
            status, response = res.next_chunk()
            print(" ----- response ----- ".upper())
            print(response)
            if response is not None:
                if 'id' in response:
                    print('Video id "%s" was successfully uploaded.' % response['id'])
                    result = 'Success'
                else:
                    print('The upload failed with an unexpected response: %s' % response)
                    result = f'The upload failed with an unexpected response: {response}'
            else:
                result = 'There is no response'

            os.remove(file_path)
            print(f'Deleted file at {file_path}')

            if result == 'Success':
                self.isPublish = True
                raise ValidationError("Successfully upload video to youtube!")
            else:
                raise ValidationError(f"{result}")

    @staticmethod
    def build_youtube_obj(obj, client_id, client_secret):
        data = {
            "token": obj.access_token,
            "refresh_token": obj.refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": YOUTUBE_API_SCOPES,
            "expiry": obj.access_token_expiry.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        credentials = Credentials.from_authorized_user_info(data)

        return build('youtube', 'v3', credentials=credentials)
