import datetime

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

    def name_get(self):
        res = []
        for record in self:
            name = record.username
            res.append((record.id, name))
        return res