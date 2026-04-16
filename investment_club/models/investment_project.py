# investment_club/models/investment_project.py
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta  # ⚠️ مهم للشهور


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
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        required=True
    )
    
    share_value = fields.Float(string='Share Value', required=True)
    
    # ===== إعدادات العوائد =====
    return_calculation_type = fields.Selection([
        ('fixed_monthly', 'Fixed Monthly'),      
        ('fixed_quarterly', 'Fixed Quarterly'),  
        ('fixed_yearly', 'Fixed Yearly'),        
        ('custom', 'Custom Schedule'),           
        ('capital_plus_return', 'Capital + Return'),  
        ('grace_period', 'Grace Period + Monthly'),  # 3 شهور سكون + شهري
    ], string='Return Calculation Type', default='fixed_monthly', required=True)
    
    # ⚠️ التغيير: فترة السكون بالشهور مش بالأيام
    grace_period_months = fields.Integer(
        string='Grace Period (Months)',
        help='عدد الشهور قبل بدء العوائد (مثلاً 3 شهور)',
        default=3
    )
    
    # ⚠️ نحتفظ بالأيام للحالات الخاصة
    grace_period_days = fields.Integer(
        string='Grace Period (Days)',
        help='فترة الانتظار قبل بدء العوائد (للتوافق مع القديم)',
        default=0
    )
    
    return_period_days = fields.Integer(
        string='Return Period (Days)',
        help='عدد الأيام بين كل دفع عائد (للجدول المخصص فقط)',
        default=30
    )
    
    return_percentage = fields.Float(
        string='Return Percentage (%)',
        help='نسبة العائد السنوية على الاستثمار',
        default=0.0
    )
    
    capital_return_period = fields.Integer(
        string='Capital Return Period (Months)',
        help='بعد كم شهر يرجع رأس المال كامل',
        default=0
    )
    
    fixed_return_amount = fields.Float(
        string='Fixed Return Amount per Period',
        help='المبلغ الثابت اللي العميل ياخده كل فترة',
        default=0.0
    )
    
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