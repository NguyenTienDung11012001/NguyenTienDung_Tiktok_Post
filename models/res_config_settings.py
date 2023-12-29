from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    client_id = fields.Char('Client Id', config_parameter='tiktok_post.client_id')
    client_secret = fields.Char('Client Secret', config_parameter='tiktok_post.client_secret')
