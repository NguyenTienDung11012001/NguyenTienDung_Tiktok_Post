from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tiktok_client_id = fields.Char('Client Id', config_parameter='tiktok_post.client_id')
    tiktok_client_secret = fields.Char('Client Secret', config_parameter='tiktok_post.client_secret')

    google_client_id = fields.Char('Client Id', config_parameter='tiktok_post.google_client_id')
    google_client_secret = fields.Char('Client Secret', config_parameter='tiktok_post.google_client_secret')
