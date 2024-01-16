import json

import werkzeug.utils
import requests
import hashlib
import os
from odoo import http

from datetime import datetime, timedelta


class TiktokPost(http.Controller):
    @http.route('/tiktok', type='http', auth='public')
    def tiktok(self, type):
        file_path = os.path.join(os.path.dirname(__file__), "tiktok_config.json")

        client_id = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_id')
        if not client_id:
            config_data = json.load(open(file_path, "r"))
            client_id = config_data.get('client_id')
            client_secret = config_data.get('client_secret')
            http.request.env['ir.config_parameter'].sudo().set_param('tiktok_post.client_id', client_id)
            http.request.env['ir.config_parameter'].sudo().set_param('tiktok_post.client_secret', client_secret)

        ads_url = f'https://business-api.tiktok.com/portal/auth?app_id={client_id}&state={type}&redirect_uri=https%3A%2F%2Fodoo.website%2Ftiktok%2Ffinalize%2F'
        account_url = f'https://www.tiktok.com/v2/auth/authorize?client_key={client_id}&scope=user.info.basic%2Cuser.info.username%2Cuser.info.stats%2Cuser.account.type%2Cuser.insights%2Cvideo.list%2Cvideo.insights%2Ccomment.list%2Ccomment.list.manage%2Cvideo.publish&response_type=code&redirect_uri=https%3A%2F%2Fodoo.website%2Ftiktok%2Ffinalize%2F&state=account'
        if type[:7] == 'account':
            return werkzeug.utils.redirect(account_url)
        elif type[:7] == 'ads0000':
            return werkzeug.utils.redirect(ads_url)
        return werkzeug.utils.redirect('/web')

    @http.route('/tiktok/finalize/', type='http', auth='public')
    def tiktok_finalize(self, **kw):
        print(kw)
        if kw.get('state')[:7] == 'account':
            self.get_account_info(kw)
        elif kw.get('state')[:7] == 'ads0000':
            self.get_business_info(kw)
        action_id = http.request.env.ref('tiktok_post.tiktok_access_token_act').id
        return werkzeug.utils.redirect(f'/web#view_type=list&model=google.access.token&action={action_id}')

    @staticmethod
    def get_account_info(kw):
        print('*******************************************************************************************************')
        # ----------------------- GET ACCESS TOKEN -----------------------
        client_id = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_id')
        client_secret = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_secret')
        url = "https://business-api.tiktok.com/open_api/v1.3/tt_user/oauth2/token/"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'auth_code': kw.get('code'),
            'redirect_uri': 'https://odoo.website/tiktok/finalize/',
        }
        response = requests.post(url=url, json=data, headers=headers).json()

        if response.get('code') == 0:
            print(" ----- access token response ----- ".upper())
            print(response)
            a_data = response.get('data')

            # ----------------------- USER DATA -----------------------
            url = 'https://business-api.tiktok.com/open_api/v1.3/business/get/'
            params = {
                'business_id': response.get('data').get('open_id'),
                'fields': '["username","display_name", "is_business_account"]',
            }
            headers = {
                'Access-Token': response.get('data').get('access_token')
            }
            res = requests.get(url, params=params, headers=headers).json()

            if res.get('code') == 0:
                print(" ----- user data response ----- ".upper())
                print(res)
                u_data = res.get('data')

                tiktok_model = http.request.env['tiktok.access.token'].sudo().search(
                    [('username', '=', u_data.get('username'))])
                if not tiktok_model:
                    tiktok_model.create({
                        'username': u_data.get('username'),
                        'display_name': u_data.get('display_name'),
                        'access_token': a_data.get('access_token'),
                        'open_id': a_data.get('open_id'),
                        'access_token_time_out': datetime.now() + timedelta(seconds=a_data.get('expires_in')),
                        'refresh_token': a_data.get('refresh_token'),
                        'refresh_token_timeout': datetime.now() + timedelta(
                            seconds=a_data.get('refresh_token_expires_in')),
                        'is_business_account': u_data.get('is_business_account'),
                    })
                else:
                    print(" ----- account is exist ----- ".upper())

            else:
                print(" ----- user data error ----- ".upper())
                print(res)
        else:
            print(" ----- access token error ----- ".upper())
            print(response)

    @staticmethod
    def get_business_info(kw):
        print('*******************************************************************************************************')
        client_id = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_id')
        client_secret = http.request.env['ir.config_parameter'].sudo().get_param('tiktok_post.client_secret')

        url = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "secret": client_secret,
            "app_id": client_id,
            "auth_code": kw.get('auth_code'),
        }
        response = requests.post(url, json=data, headers=headers).json()
        print(" ----- ads authentication response ----- ".upper())
        print(response)
        if response.get('code') == 0:
            data = response.get('data')
            username = kw.get('state')[7:]
            tiktok_model = http.request.env['tiktok.access.token'].search([('username', '=', username)])
            tiktok_model.write({
                'advertiser_id': data.get('advertiser_ids')[0],
                'business_account_access_token': data.get('access_token'),
            })
            uid = tiktok_model.id
            action_id = http.request.env.ref('tiktok_post.tiktok_access_token_act').id
            print(action_id, uid)
            return werkzeug.utils.redirect(f'/web#view_type=form&model=google.access.token&action={action_id}&id={uid}')
        else:
            print(" ----- Code ----- ".upper())
            print(response.get('code'))
            print(" ----- Response ----- ".upper())
            print(response)

        # if response.get('code') == 0:
        #     a_data = response.get('data')
        #     access_token = a_data.get('access_token')
        #     advertiser_id = a_data.get('advertiser_ids')[0]
        #     video_file = ("vid.mp4", open("/home/adpttq113/Downloads/vid.mp4", "rb"))
        #     video_signature = self.calculate_md5('/home/adpttq113/Downloads/vid.mp4')
        #     print(" ----- video_signature ----- ".upper())
        #     print(video_signature)
        #
        #     url = "https://business-api.tiktok.com/open_api/v1.3/file/video/ad/upload/"
        #     headers = {
        #         "Access-Token": access_token,
        #         "Content-Type": "multipart/form-data"
        #     }
        #     data = {
        #         "upload_type": 'UPLOAD_BY_FILE',
        #         "advertiser_id": f'{advertiser_id}',
        #         "file_name": "sarah_test-through-file",
        #         "video_signature": video_signature,
        #     }
        #     file = {
        #         "video_file": video_file
        #     }
        #     response = requests.post(url, data=data, headers=headers, files=file)
        #     print(f'CODE: {response.status_code}')
        #     print(response.text)
        # else:
        #     print(" ----- Code ----- ".upper())
        #     print(response.get('code'))
        #     print(" ----- Response ----- ".upper())
        #     print(response)
