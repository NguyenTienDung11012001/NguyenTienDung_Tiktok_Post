import datetime
import requests

from odoo import fields, models, api, http


class TiktokModel(models.Model):
    _name = 'video.model'
    _description = 'Tiktok video'

    name = fields.Char(string='Video title', required=True)
    video_url = fields.Char(string='Video URL', required=True)
    schedule = fields.Datetime(string='Schedule', required=True)
    is_publish = fields.Boolean(string='Is publish', default=False, readonly=True)
    tiktok_account = fields.Many2one('tiktok.access.token', string='Tiktok Account', required=True)

    @api.depends('action_done', 'tiktok_account')
    def _compute_state(self):
        for rec in self:
            if not rec.tiktok_account:
                rec.state = 'draft'
                if rec.action_done:
                    rec.state = 'done'
            else:
                rec.state = 'pending'

    def set_is(self):
        self.is_publish = False

    @api.model
    def post_video(self):
        videos = self.search([('schedule', '<', fields.Datetime.now()),
                              ('is_publish', '=', False)])

        if videos:
            for video in videos:
                if video.tiktok_account.access_token_time_out < datetime.datetime.now():
                    access_token = self.renew_access_token(video.tiktok_account,
                                                           video.tiktok_account.refresh_token)
                else:
                    access_token = video.tiktok_account.access_token

                result = self.publish_video(access_token, video.tiktok_account.open_id,
                                            video.video_url, video.name)
                if result == 0:
                    video.is_publish = True

    @staticmethod
    def publish_video(access_token, open_id, video_url, caption):
        url = "https://business-api.tiktok.com/open_api/v1.3/business/video/publish/"
        headers = {
            'Access-Token': access_token,
            "Content-Type": "application/json",
        }
        data = {
            'business_id': open_id,
            'video_url': video_url,
            'post_info': {
                "caption": caption,
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False
            }
        }

        response = requests.post(url=url, json=data, headers=headers).json()
        print(" ----- publish video response ----- ".upper())
        print(response)
        return response.get('code')

    @staticmethod
    def renew_access_token(model, refresh_token):
        client_id = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_id')
        client_secret = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_secret')

        url = "https://business-api.tiktok.com/open_api/v1.3/tt_user/oauth2/refresh_token/"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        res = requests.post(url=url, json=data, headers=headers).json()

        if res.get('code') == 0:
            print(" ----- renew access token response ----- ".upper())
            print(res)
            data = res.get('data')

            model.write({
                'access_token': data.get('access_token'),
                'access_token_time_out': datetime.datetime.now() + datetime.timedelta(seconds=data.get('expires_in')),
                'refresh_token': data.get('refresh_token'),
                'refresh_token_timeout': datetime.datetime.now() + datetime.timedelta(
                    seconds=data.get('refresh_token_expires_in')),
            })

        return data.get('access_token')
