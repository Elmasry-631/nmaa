from odoo import models, fields, api


class ContractAmendment(models.Model):
    _name = 'contract.amendment'
    _description = 'Contract Amendment'
    _order = 'date desc'

    contract_id = fields.Many2one(
        'sale.contract', string='Contract',
        ondelete='cascade', required=True, tracking=True
    )
    name = fields.Char(
        string='Amendment Reference',
        required=True, default='New',
        copy=False, readonly=True, tracking=True
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.today, tracking=True
    )
    description = fields.Text(
        string='Description', required=True, tracking=True,
        help='Describe what was changed in this amendment'
    )
    previous_value = fields.Text(
        string='Previous Value',
        help='Value before the amendment'
    )
    new_value = fields.Text(
        string='New Value',
        help='Value after the amendment'
    )
    user_id = fields.Many2one(
        'res.users', string='Modified By',
        default=lambda self: self.env.uid, tracking=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'contract.amendment') or 'New'
        record = super().create(vals)
        record.contract_id.message_post(
            body=f"<b>&#x1F4DD; Amendment {record.name}</b><br/>{record.description}"
        )
        record.contract_id.version += 1
        return record
