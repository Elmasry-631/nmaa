# investment_club/models/investment_project.py
from odoo import models, fields, api


class InvestmentProject(models.Model):
    _name = 'investment.project'
    _description = 'Investment Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Project Name', required=True, tracking=True)
    code = fields.Char(string='Project Code', readonly=True, copy=False)
    
    club_id = fields.Many2one(
        'investment.club',
        string='Club',
        required=True,
        ondelete='cascade'
    )
    
    # Analytic Account للمشروع
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        required=True,
        help='حساب تحليلي لتتبع إيرادات ومصروفات المشروع'
    )
    
    # بيانات مالية - فاضية في البداية
    share_value = fields.Float(string='Share Value', required=True)
    monthly_return = fields.Float(string='Monthly Return', required=True)
    
    investors_per_branch = fields.Integer(string='Investors per Branch', default=8)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    description = fields.Text(string='Description')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('investment.project') or 'New'
        return super(InvestmentProject, self).create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_close(self):
        self.write({'state': 'closed'})