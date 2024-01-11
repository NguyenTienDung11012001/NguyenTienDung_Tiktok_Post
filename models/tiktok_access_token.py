import datetime

import werkzeug.utils
from odoo.exceptions import ValidationError
from odoo import fields, models, api


class AccessToken(models.Model):
    _name = 'tiktok.access.token'
    _description = 'Tiktok Access Token'

    username = fields.Char(string='Username', readonly=True, required=True)
    display_name = fields.Char(string='Display Name', readonly=True, required=True)
    open_id = fields.Char(string='Business ID', readonly=True, required=True)
    access_token = fields.Char(string='Access Token', readonly=True, required=True)
    access_token_time_out = fields.Datetime(string='Access Token Timeout', readonly=True, required=True)
    refresh_token = fields.Char(string='Refresh Token', readonly=True, required=True)
    refresh_token_timeout = fields.Datetime(string='Refresh Token Timeout', readonly=True, required=True)
    is_business_account = fields.Boolean(string='Is Business Account', readonly=True, required=True)
    advertiser_id = fields.Char(string="Advertiser ID", readonly=True)
    business_account_access_token = fields.Char(string='Business Account Access Token', readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = record.username
            res.append((record.id, name))
        return res

    def get_advertiser_id(self):
        if self.is_business_account:
            return {
                "url": f"/tiktok?type=ads0000{self.username}",
                "type": "ir.actions.act_url",
                "target": 'self',
            }
        else:
            raise ValidationError("Your account must be a business account")