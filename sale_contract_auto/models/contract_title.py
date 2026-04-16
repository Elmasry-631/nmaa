from odoo import models, fields


class ContractTitle(models.Model):
    _name = 'sale.contract.title'
    _description = 'Contract Title'
    _rec_name = "name"

    name = fields.Char(string='Contract Title', required=True, tracking=True)
