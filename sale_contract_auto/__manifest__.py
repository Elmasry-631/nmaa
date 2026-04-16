{
    'name': "Sale Contract Auto",
    'version': '2.0',
    'category': 'Sales',
    'summary': "Advanced contract management with approval workflow, expiry tracking, payment schedules, and more",
    'description': """
    
Sale Contract Auto v2.0
========================

Features:
---------
• Create customer contracts linked with sale orders
• Multi-level approval workflow (Draft → Confirmed → Financial → Legal → Finished)
• Contract expiry dates with auto-renewal and scheduled notifications
• Dynamic template placeholders ({{partner_name}}, {{amount}}, etc.)
• Clause library for reusable contract terms
• Invoice generation from contracts and payment installments
• Payment schedules with installment tracking
• Contract amendments with version control
• Document management (required/optional uploads)
• QR code verification on printed contracts
• Company stamp on reports
• Customer portal for viewing and signing contracts
• Kanban dashboard with expiry warnings
• Automated email notifications on state changes
• Arabic RTL support with formatted dates
""",

    'author': "Ibrahim Elmasry",
    'website': "https://www.woledge.com",
    'license': 'LGPL-3',

    'depends': [
        'base',
        'sale_management',
        'account',
        'portal',
        'mail',
    ],

    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/mail_templates.xml',
        'data/contract_data.xml',
        #
        # Sequences
        'views/ir_sequence.xml',

        # Views
        'views/res_partner_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/dashboard_template.xml',

        # Reports
        'report/contract_report.xml',
        'report/contract_print_template.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
