# investment_club/models/res_config_settings.py
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # === Membership Settings ===
    default_membership_product_id = fields.Many2one(
        'product.product',
        string='Default Membership Product',
        config_parameter='investment_club.default_membership_product_id',
        domain="[('type', '=', 'service')]",
        help='المنتج الافتراضي للعضوية الجديدة'
    )
    
    default_subscription_product_id = fields.Many2one(
        'product.product',
        string='Default Subscription Product',
        config_parameter='investment_club.default_subscription_product_id',
        domain="[('type', '=', 'service')]",
        help='المنتج الافتراضي للتجديد السنوي'
    )
    
    default_subscription_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Default Subscription Period', 
       config_parameter='investment_club.default_subscription_period',
       default='yearly')
    
    # === Financial Settings ===
    default_payment_journal_id = fields.Many2one(
        'account.journal',
        string='Default Payment Journal',
        config_parameter='investment_club.default_payment_journal_id',
        domain="[('type', 'in', ('bank', 'cash'))]",
        help='الحساب الافتراضي لتسجيل المدفوعات'
    )
    
    return_payment_journal_id = fields.Many2one(
        'account.journal',
        string='Returns Payment Journal',
        config_parameter='investment_club.return_payment_journal_id',
        domain="[('type', 'in', ('bank', 'cash'))]",
        help='الحساب الافتراضي لدفع العوائد للعملاء'
    )
    
    # === Club Settings ===
    auto_activate_projects = fields.Boolean(
        string='Auto Activate Projects',
        config_parameter='investment_club.auto_activate_projects',
        default=False,
        help='تفعيل المشاريع تلقائياً عند الإنشاء'
    )
    
    auto_renewal_days_before = fields.Integer(
        string='Auto Renewal Days Before',
        config_parameter='investment_club.auto_renewal_days_before',
        default=7,
        help='عدد الأيام قبل الانتهاء لإشعار التجديد'
    )
    
    # === Notification Settings ===
    enable_renewal_notifications = fields.Boolean(
        string='Enable Renewal Notifications',
        config_parameter='investment_club.enable_renewal_notifications',
        default=True
    )
    
    enable_payment_notifications = fields.Boolean(
        string='Enable Payment Notifications',
        config_parameter='investment_club.enable_payment_notifications',
        default=True
    )