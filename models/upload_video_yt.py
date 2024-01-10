import time
import random

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
    path = fields.Char(string='Path', required=True)
    channel = fields.Many2one('google.access.token', string='Youtube Channel', required=True)

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

            res = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=MediaFileUpload(self.path, chunksize=-1, resumable=True))

            result = self.resumable_upload(res)

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

    @staticmethod
    def resumable_upload(request):
        result = None
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print('Uploading file...')
                status, response = request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print('Video id "%s" was successfully uploaded.' % response['id'])
                        result = 'Success'
                    else:
                        result = 'Fail'
                        exit('The upload failed with an unexpected response: %s' % response)
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
                else:
                    result = 'A retriable HTTP error'
            except [500, 502, 503, 504] as e:
                error = 'A retriable error occurred: %s' % e

            if error is not None:
                print(error)
                retry += 1
                if retry > 10:
                    exit('No longer attempting to retry.')
                    result = error

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print('Sleeping %f seconds and then retrying...' % sleep_seconds)
                time.sleep(sleep_seconds)

        return result
