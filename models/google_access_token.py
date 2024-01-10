from odoo import fields, models, api


class GoogleModel(models.Model):
    _name = 'google.access.token'
    _description = 'Google Access Token'

    username = fields.Char(string='Username', readonly=True, required=True)
    display_name = fields.Char(string='Display Name', readonly=True, required=True)
    access_token = fields.Char(string='Access Token', readonly=True, required=True)
    access_token_expiry = fields.Datetime(string='Access Token Expiry', readonly=True, required=True)
    refresh_token = fields.Char(string='Refresh Token', readonly=True, required=True)

    def name_get(self):
        res = []
        for record in self:
            name = record.username
            res.append((record.id, name))
        return res 
