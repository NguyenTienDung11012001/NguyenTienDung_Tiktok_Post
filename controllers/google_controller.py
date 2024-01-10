import json
import datetime
from odoo import http
from odoo.http import request
import werkzeug
import traceback
import logging
import os
import random
import time

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

_logger = logging.getLogger(__name__)

YOUTUBE_API_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]
CLIENT_SECRETS_FILE = 'client_secret.json'
REDIRECT_URI = 'https://odoo.website/google-callback'


class GooglePost(http.Controller):
    @staticmethod
    def init_google_flow(scopes):
        file_path = os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE)
        flow = Flow.from_client_secrets_file(file_path, scopes=scopes)
        flow.redirect_uri = REDIRECT_URI
        
        with open(file_path, "r") as json_file:
            client_config = json.load(json_file)
            client_id = client_config.get('web').get('client_id')
            client_secret = client_config.get('web').get('client_secret')
            request.env['ir.config_parameter'].sudo().set_param('tiktok_post.google_client_id', client_id)
            request.env['ir.config_parameter'].sudo().set_param('tiktok_post.google_client_secret', client_secret)

        return flow

    @http.route('/google', auth='public')
    def google_ads_auth(self):
        try:
            flow = self.init_google_flow(YOUTUBE_API_SCOPES)

            authorization_url, state = flow.authorization_url(
                access_type='offline',
                prompt="consent",
                include_granted_scopes='false')

            return werkzeug.utils.redirect(authorization_url)
        except Exception as e:
            _logger.error(traceback.format_exc())

        action_id = request.env.ref('tiktok_post.google_access_token_act').id
        return werkzeug.utils.redirect(f'/web#view_type=list&model=google.access.token&action={action_id}')

    @http.route('/google-callback', auth='public')
    def google_ads_finalize(self, **kw):
        flow = self.init_google_flow(kw.get('scope'))
        flow.fetch_token(code=kw.get('code'))
        credentials = flow.credentials

        # --------------------------------- GET YOUTUBE CHANNEL INFO ---------------------------------
        youtube = build(
            'youtube', 'v3', credentials=credentials)

        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        res = request.execute()

        item = res.get('items')
        snippet = item[0].get('snippet')
        username = snippet.get('customUrl')

        google_model = http.request.env['google.access.token'].search([('username', '=', username)])
        if not google_model:
            google_model.create({
                'username': snippet.get('customUrl'),
                'display_name': snippet.get('title'),
                'access_token': credentials.token,
                'access_token_expiry': credentials.expiry,
                'refresh_token': credentials.refresh_token,
            })
        else:
            print(" ----- account is exist ----- ".upper())

        action_id = http.request.env.ref('tiktok_post.google_access_token_act').id
        return werkzeug.utils.redirect(f'/web#view_type=list&model=google.access.token&action={action_id}')

    # @staticmethod
    # def build_youtube_obj(obj):
    #     data = {
    #         "token": obj.access_token,
    #         "refresh_token": obj.refresh_token,
    #         "token_uri": "https://oauth2.googleapis.com/token",
    #         "client_id": request.env['ir.config_parameter'].sudo().get_param('tiktok_post.google_client_id'),
    #         "client_secret": request.env['ir.config_parameter'].sudo().get_param('tiktok_post.google_client_secret'),
    #         "scopes": YOUTUBE_API_SCOPES,
    #         "expiry": obj.access_token_expiry.strftime("%Y-%m-%dT%H:%M:%S"),
    #     }
    #
    #     credentials = Credentials.from_authorized_user_info(data)
    #
    #     return build('youtube', 'v3', credentials=credentials)
    #
    # @staticmethod
    # def resumable_upload(request):
    #     response = None
    #     error = None
    #     retry = 0
    #     while response is None:
    #         try:
    #             print('Uploading file...')
    #             status, response = request.next_chunk()
    #             if response is not None:
    #                 if 'id' in response:
    #                     print('Video id "%s" was successfully uploaded.' % response['id'])
    #                 else:
    #                     exit('The upload failed with an unexpected response: %s' % response)
    #         except HttpError as e:
    #             if e.resp.status in [500, 502, 503, 504]:
    #                 error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status,
    #                                                                      e.content)
    #             else:
    #                 raise
    #         except [500, 502, 503, 504] as e:
    #             error = 'A retriable error occurred: %s' % e
    #
    #         if error is not None:
    #             print(error)
    #             retry += 1
    #             if retry > 10:
    #                 exit('No longer attempting to retry.')
    #
    #             max_sleep = 2 ** retry
    #             sleep_seconds = random.random() * max_sleep
    #             print('Sleeping %f seconds and then retrying...' % sleep_seconds)
    #             time.sleep(sleep_seconds)
    #     return response['id']
    #
    # @http.route('/test-gg', auth='public')
    # def test_gg(self):
    #     upload_date_time = datetime.datetime(2024, 1, 11, 12, 30, 0).isoformat()
    #     body = {
    #         'snippet': {
    #             'categoryId': 10,
    #             'title': 'best music on the youtube | happy mood mix | AMP',
    #             'description': "test",
    #             'tags': ['Travel', 'video test', 'Travel Tips']
    #         },
    #         'status': {
    #             'privacyStatus': 'private',
    #             'publishAt': upload_date_time,
    #         },
    #     }
    #
    #     google_model = http.request.env['google.access.token'].search([('username', '=', '@dungtien2687')])
    #
    #     youtube = self.build_youtube_obj(google_model)
    #
    #     res = youtube.videos().insert(
    #         part='snippet,status',
    #         body=body,
    #         media_body=MediaFileUpload('/home/adpttq113/Downloads/vid.mp4', chunksize=-1, resumable=True))
    #
    #     return self.resumable_upload(res)
