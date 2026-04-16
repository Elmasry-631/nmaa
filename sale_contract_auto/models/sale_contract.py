from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta
import secrets


class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Customer Sale Contract'
    _inherit = ['mail.thread', 'portal.mixin']

    # ==============================
    # BASIC FIELDS
    # ==============================
    name = fields.Char(
        string='Contract Reference',
        required=True, copy=False, readonly=True,
        default='New', tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        required=True, tracking=True
    )
    sale_order_id = fields.Many2one(
        'sale.order', string='Sales Order', tracking=True
    )
    contract_date = fields.Date(
        string='Contract Date',
        default=fields.Date.context_today, tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id, tracking=True
    )
    agreement_terms = fields.Html(
        string='Agreement Terms'
    )
    contract_line_ids = fields.One2many(
        'sale.contract.line', 'contract_id',
        string='Contract Lines', tracking=True
    )
    contract_title_name = fields.Many2one(
        'sale.contract.title', string='Contract Title', tracking=True
    )
    contract_template_id = fields.Many2one(
        'contract.template', string='Contract Template', tracking=True
    )
    note = fields.Text(string='Notes')
    access_token = fields.Char('Security Token', copy=False)

    # ==============================
    # STATE
    # ==============================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('financial_approved', 'Financial Approved'),
        ('legal_approved', 'Legal Approved'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    # ==============================
    # FINANCIAL FIELDS
    # ==============================
    subtotal_total = fields.Monetary(
        string='Subtotal Total',
        compute='_compute_subtotal_total',
        currency_field='currency_id', store=True,
    )
    amount_total = fields.Monetary(
        string='Total Amount',
        compute='_compute_amount_total', store=True, tracking=True , readony=False
    )
    invoice_ids = fields.Many2many(
        'account.move', string='Invoices',
        compute='_compute_invoice_ids'
    )
    invoice_count = fields.Integer(
        string='Invoice Count', compute='_compute_invoice_ids'
    )
    invoiced_amount = fields.Monetary(
        string='Invoiced Amount',
        compute='_compute_invoiced_amount',
        currency_field='currency_id', store=True
    )
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        compute='_compute_invoiced_amount',
        currency_field='currency_id', store=True
    )

    # ==============================
    # DATE FIELDS (Expiry & Renewal)
    # ==============================
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.context_today, tracking=True
    )
    end_date = fields.Date(
        string='End Date', tracking=True
    )
    auto_renew = fields.Boolean(
        string='Auto Renew', default=False, tracking=True
    )
    auto_renew_days = fields.Integer(
        string='Notify Before Expiry (Days)',
        default=30, tracking=True,
        help='Number of days before expiry to send renewal notification'
    )
    days_remaining = fields.Integer(
        string='Days Remaining',
        compute='_compute_expiry_info'
    )
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_expiry_info'
    )
    can_be_renewed = fields.Boolean(
        string='Can Be Renewed',
        compute='_compute_expiry_info'
    )

    # ==============================
    # PARTIES
    # ==============================
    first_party_id = fields.Many2one(
        'res.partner', string="First Party",
        default=lambda self: self.env.company.partner_id,
    )
    first_party_name = fields.Char(
        string='First Party',
        compute='_compute_first_party_info', store=True,
    )
    first_party_registry = fields.Char(
        string='Company Registry',
        compute='_compute_first_party_info', store=True,
    )
    first_party_address = fields.Char(
        string='Address',
        compute='_compute_first_party_info', store=True,
    )
    second_party_id = fields.Many2one(
        'res.partner', string="Second Party",
        related='partner_id', readonly=True,
    )
    second_party_name = fields.Char(
        string='Second Party',
        related='partner_id.name', readonly=True
    )
    second_party_address = fields.Char(
        string='Second Party Address',
        compute='_compute_second_party_address'
    )
    second_party_id_card = fields.Char(
        string='ID Card',
        related='partner_id.card_id', readonly=True
    )

    # ==============================
    # SIGNATURES
    # ==============================
    first_party_signature = fields.Binary(string='First Party Signature')
    second_party_signature = fields.Binary(string='Second Party Signature')

    # ==============================
    # PAYMENT SCHEDULE
    # ==============================
    payment_installments = fields.Integer(
        string='Number of Installments',
        tracking=True,
        help='Number of payment installments'
    )
    payment_interval_days = fields.Integer(
        string='Interval Between Installments (Days)',
        default=30, tracking=True
    )
    payment_schedule_ids = fields.One2many(
        'contract.payment.schedule', 'contract_id',
        string='Payment Schedule'
    )

    # ==============================
    # DOCUMENTS
    # ==============================
    document_ids = fields.One2many(
        'contract.document', 'contract_id',
        string='Documents'
    )
    all_documents_uploaded = fields.Boolean(
        string='All Required Documents Uploaded',
        compute='_compute_all_documents_uploaded'
    )

    # ==============================
    # AMENDMENTS
    # ==============================
    amendment_ids = fields.One2many(
        'contract.amendment', 'contract_id',
        string='Amendments'
    )
    amendment_count = fields.Integer(
        string='Amendment Count',
        compute='_compute_amendment_count'
    )
    source_contract_id = fields.Many2one(
        'sale.contract', string='Source Contract',
        help='If this is a renewal/amendment, reference to original contract'
    )
    version = fields.Integer(
        string='Version', default=1, tracking=True
    )

    # ==============================
    # COMPANY STAMP
    # ==============================
    company_stamp = fields.Binary(
        string='Company Stamp',
        compute='_compute_company_stamp',
    )

    # ==============================
    # QR CODE
    # ==============================
    qr_code_url = fields.Char(
        string='QR Code URL',
        compute='_compute_qr_code_url'
    )

    # ==============================
    # COMPUTE: Financial Totals
    # ==============================
    @api.depends('contract_line_ids.price_subtotal')
    def _compute_subtotal_total(self):
        for contract in self:
            contract.subtotal_total = sum(
                contract.contract_line_ids.mapped('price_subtotal')
            )

    @api.depends('subtotal_total')
    def _compute_amount_total(self):
        for contract in self:
            contract.amount_total = contract.subtotal_total

    @api.depends('invoice_ids', 'invoice_ids.payment_state')
    def _compute_invoiced_amount(self):
        for contract in self:
            invoices = contract.invoice_ids
            invoiced = sum(
                inv.amount_total for inv in invoices
                if inv.state in ('draft', 'posted')
            )
            paid = sum(
                inv.amount_total_signed for inv in invoices
                if inv.payment_state in ('paid', 'in_payment')
            )
            contract.invoiced_amount = abs(paid)
            contract.remaining_amount = contract.amount_total - abs(paid)

    @api.depends('sale_order_id')
    def _compute_invoice_ids(self):
        for contract in self:
            invoices = self.env['account.move'].search([
                ('contract_id', '=', contract.id),
                ('move_type', '=', 'out_invoice'),
            ])
            contract.invoice_ids = invoices
            contract.invoice_count = len(invoices)

    # ==============================
    # COMPUTE: Expiry
    # ==============================
    @api.depends('end_date', 'auto_renew_days')
    def _compute_expiry_info(self):
        today = fields.Date.today()
        for rec in self:
            if rec.end_date:
                delta = (rec.end_date - today).days
                rec.days_remaining = delta
                rec.is_expired = delta < 0
                rec.can_be_renewed = delta <= rec.auto_renew_days
            else:
                rec.days_remaining = False
                rec.is_expired = False
                rec.can_be_renewed = False

    # ==============================
    # COMPUTE: Parties
    # ==============================
    @api.depends('first_party_id', 'first_party_id.name', 'first_party_id.company_registry',
                 'first_party_id.street', 'first_party_id.street2', 'first_party_id.city',
                 'first_party_id.state_id', 'first_party_id.country_id')
    def _compute_first_party_info(self):
        for rec in self:
            partner = rec.first_party_id
            if partner:
                rec.first_party_name = partner.name
                rec.first_party_registry = partner.company_registry or ''
                address_parts = [
                    partner.street,
                    partner.street2,
                    partner.city,
                    partner.state_id.name if partner.state_id else False,
                    partner.country_id.name if partner.country_id else False,
                ]
                rec.first_party_address = " - ".join(filter(None, address_parts))
            else:
                rec.first_party_name = self.env.company.name
                rec.first_party_registry = self.env.company.company_registry or ''
                rec.first_party_address = " - ".join(filter(None, [
                    self.env.company.street,
                    self.env.company.street2,
                    self.env.company.city,
                    self.env.company.state_id.name if self.env.company.state_id else False,
                    self.env.company.country_id.name if self.env.company.country_id else False,
                ]))

    @api.depends('partner_id')
    def _compute_second_party_address(self):
        for rec in self:
            p = rec.partner_id
            if p:
                address_parts = [
                    p.street, p.street2, p.city,
                    p.state_id.name if p.state_id else False,
                    p.country_id.name if p.country_id else False,
                ]
                rec.second_party_address = " - ".join(filter(None, address_parts))
            else:
                rec.second_party_address = ""

    # ==============================
    # COMPUTE: Documents
    # ==============================
    @api.depends('document_ids', 'document_ids.uploaded', 'document_ids.required')
    def _compute_all_documents_uploaded(self):
        for contract in self:
            required = contract.document_ids.filtered('required')
            if required:
                contract.all_documents_uploaded = all(d.uploaded for d in required)
            else:
                contract.all_documents_uploaded = True

    # ==============================
    # COMPUTE: Amendments
    # ==============================
    def _compute_amendment_count(self):
        for contract in self:
            contract.amendment_count = len(contract.amendment_ids)

    # ==============================
    # COMPUTE: Company Stamp
    # ==============================
    def _compute_company_stamp(self):
        for rec in self:
            param = self.env['ir.config_parameter'].sudo().get_param(
                'sale_contract_auto.company_stamp')
            if param:
                rec.company_stamp = param
            else:
                rec.company_stamp = False

    # ==============================
    # COMPUTE: QR Code URL
    # ==============================
    def _compute_qr_code_url(self):
        for contract in self:
            contract.qr_code_url = contract.get_portal_url()

    # ==============================
    # ONCHANGE TEMPLATE
    # ==============================
    @api.onchange('contract_template_id')
    def _onchange_contract_template(self):
        if self.contract_template_id:
            template = self.contract_template_id
            self.agreement_terms = template._render_template(
                template.content, 'sale.contract', self.id
            )

    # ==============================
    # CREATE
    # ==============================

    def _generate_access_token(self):
        """توليد توكن عشوائي"""
        return secrets.token_urlsafe(32)  # يولد توكن 32 حرف عشوائي

    @api.model
    def create(self, vals):
        if not vals.get('access_token'):
            vals['access_token'] = self._generate_access_token()
        return super(SaleContract, self).create(vals)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'sale.contract') or 'New'

        if vals.get('contract_template_id') and not vals.get('agreement_terms'):
            template = self.env['contract.template'].browse(
                vals['contract_template_id'])
            if template.exists():
                vals['agreement_terms'] = template.content

        if not vals.get('access_token'):
            vals['access_token'] = self._generate_access_token()

        return super().create(vals)

    # ==============================
    # WRITE
    # ==============================
    def write(self, vals):
        if vals.get('contract_template_id'):
            template = self.env['contract.template'].browse(
                vals['contract_template_id'])
            if template.exists():
                vals['agreement_terms'] = template._render_template(
                    template.content, 'sale.contract', self.id
                )
        return super(SaleContract, self).write(vals)

    # ==============================
    # STATE ACTIONS with Notifications
    # ==============================
    def action_set_active(self):
        for contract in self:
            contract.state = 'confirmed'
            contract.message_post(
                body="<b>Contract Confirmed</b><br/>Contract has been confirmed and sent for financial review.",
                partner_ids=contract.partner_id.ids,
                subtype_xmlid='mail.mt_comment'
            )

    def action_financial_approve(self):
        for contract in self:
            contract.state = 'financial_approved'
            contract.message_post(
                body="<b>Financial Approved</b><br/>Contract has been approved by the finance department. Awaiting legal review.",
                partner_ids=contract.partner_id.ids,
                subtype_xmlid='mail.mt_comment'
            )

    def action_legal_approve(self):
        for contract in self:
            contract.state = 'legal_approved'
            contract.message_post(
                body="<b>Legal Approved</b><br/>Contract has been approved by the legal department. Ready to finalize.",
                partner_ids=contract.partner_id.ids,
                subtype_xmlid='mail.mt_comment'
            )

    def action_finish(self):
        for contract in self:
            contract.state = 'finished'
            contract.message_post(
                body="<b>Contract Finalized</b><br/>Contract has been finalized successfully.",
                partner_ids=contract.partner_id.ids,
                subtype_xmlid='mail.mt_comment'
            )

    def action_cancel(self):
        for contract in self:
            contract.state = 'cancelled'
            contract.message_post(
                body="<b>Contract Cancelled</b><br/>Contract has been cancelled.",
                partner_ids=contract.partner_id.ids,
                subtype_xmlid='mail.mt_comment'
            )

    def action_reset_to_draft(self):
        for contract in self:
            contract.state = 'draft'
            contract.message_post(
                body="<b>Reset to Draft</b><br/>Contract has been reset to draft.",
                subtype_xmlid='mail.mt_comment'
            )

    # ==============================
    # RENEW CONTRACT
    # ==============================
    def action_renew_contract(self):
        self.ensure_one()
        if not self.end_date:
            raise UserError("Cannot renew contract without end date.")

        duration = (self.end_date - (self.start_date or self.contract_date)).days
        if duration <= 0:
            duration = 365

        new_vals = {
            'partner_id': self.partner_id.id,
            'sale_order_id': self.sale_order_id.id,
            'contract_title_name': self.contract_title_name.id,
            'contract_template_id': self.contract_template_id.id,
            'start_date': self.end_date,
            'end_date': self.end_date + timedelta(days=duration),
            'first_party_id': self.first_party_id.id,
            'agreement_terms': self.agreement_terms,
            'currency_id': self.currency_id.id,
            'amount_total': self.amount_total,
            'auto_renew': self.auto_renew,
            'auto_renew_days': self.auto_renew_days,
            'payment_installments': self.payment_installments,
            'payment_interval_days': self.payment_interval_days,
            'source_contract_id': self.id,
            'version': self.version + 1,
            'note': f'Renewed from contract {self.name}',
            'contract_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }) for line in self.contract_line_ids],
        }

        new_contract = self.create(new_vals)
        self.message_post(
            body=f"<b>Contract Renewed</b><br/>New contract created: <a href='#' data-oe-model='sale.contract' data-oe-id='{new_contract.id}'>{new_contract.name}</a>"
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewed Contract',
            'res_model': 'sale.contract',
            'view_mode': 'form',
            'res_id': new_contract.id,
            'target': 'current',
        }

    # ==============================
    # INVOICE GENERATION
    # ==============================
    def action_create_invoice(self):
        self.ensure_one()
        if self.remaining_amount <= 0:
            raise UserError("No remaining amount to invoice.")

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'contract_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': line.name or line.product_id.display_name,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }) for line in self.contract_line_ids if line.product_id],
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.message_post(
            body=f"<b>Invoice Created</b><br/>Invoice <a href='#' data-oe-model='account.move' data-oe-id='{invoice.id}'>{invoice.name}</a> has been created."
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'default_contract_id': self.id},
        }

    # ==============================
    # PAYMENT SCHEDULE
    # ==============================
    def action_generate_payment_schedule(self):
        self.ensure_one()
        if self.payment_installments and self.payment_installments > 1:
            self.payment_schedule_ids.unlink()
            amount_per = self.amount_total / self.payment_installments
            current_date = self.start_date or fields.Date.today()

            for i in range(1, self.payment_installments + 1):
                self.env['contract.payment.schedule'].create({
                    'contract_id': self.id,
                    'installment_number': i,
                    'amount': amount_per,
                    'due_date': current_date + timedelta(days=self.payment_interval_days * (i - 1)),
                })
            self.message_post(
                body=f"<b>Payment Schedule Generated</b><br/>{self.payment_installments} installments of {amount_per:.2f} {self.currency_id.name} each."
            )

    # ==============================
    # AMENDMENTS
    # ==============================
    def action_create_amendment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Amendment',
            'res_model': 'contract.amendment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_date': fields.Date.today(),
            }
        }

    def action_view_amendments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Amendments',
            'res_model': 'contract.amendment',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
        }

    # ==============================
    # SCHEDULED ACTION: Expiry Check
    # ==============================
    @api.model
    def _check_contract_expiry(self):
        """Scheduled action to check expiring contracts"""
        today = fields.Date.today()
        contracts = self.search([
            ('auto_renew', '=', True),
            ('end_date', '!=', False),
            ('state', 'not in', ['draft', 'cancelled']),
        ])

        for contract in contracts:
            if contract.end_date:
                days_left = (contract.end_date - today).days
                if days_left == contract.auto_renew_days:
                    contract.message_post(
                        body=f"<b>&#x26A0;&#xFE0F; Expiry Warning</b><br/>This contract expires in <b>{days_left} days</b> ({contract.end_date}). Please consider renewal.",
                        subtype_xmlid='mail.mt_comment'
                    )
                elif days_left == 7:
                    contract.message_post(
                        body=f"<b>&#x1F6A8; Urgent: Contract Expiring</b><br/>This contract expires in <b>7 days</b> ({contract.end_date}). Immediate action required!",
                        subtype_xmlid='mail.mt_comment'
                    )

    # ==============================
    # PORTAL URL
    # ==============================
    def _compute_access_url(self):
        super(SaleContract, self)._compute_access_url()
        for contract in self:
            contract.access_url = f'/my/contracts/{contract.id}'

    def get_portal_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/my/contracts/{self.id}"

    # ==============================
    # REPORT
    # ==============================
    def print_contract_report(self):
        self.ensure_one()
        if self.state == 'cancelled':
            raise UserError("Cannot print a cancelled contract.")
        return self.env.ref(
            'sale_contract_auto.action_print_sale_contract'
        ).report_action(self)

    # ==============================
    # EMAIL
    # ==============================
    def action_send_contract_link(self):
        for contract in self:
            if not contract.partner_id.email:
                raise UserError(
                    f"Cannot send email. Customer '{contract.partner_id.name}' has no email."
                )
            template = self.env.ref(
                'sale_contract_auto.email_template_contract_link'
            )
            template.send_mail(contract.id, force_send=True)
        return True

    # ==============================
    # ARABIC DATE
    # ==============================
    def get_arabic_date(self):
        days = {
            'Sunday': '\u0627\u0644\u0627\u062d\u062f', 'Monday': '\u0627\u0644\u0627\u062b\u0646\u064a\u0646',
            'Tuesday': '\u0627\u0644\u062b\u0644\u0627\u062b\u0627\u0621', 'Wednesday': '\u0627\u0644\u0627\u0631\u0628\u0639\u0627\u0621',
            'Thursday': '\u0627\u0644\u062e\u0645\u064a\u0633', 'Friday': '\u0627\u0644\u062c\u0645\u0639\u0629',
            'Saturday': '\u0627\u0644\u0633\u0628\u062a'
        }
        d = self.contract_date
        if not d:
            return ""
        day = days.get(d.strftime('%A'), d.strftime('%A'))
        return f"\u0627\u0646\u0647 \u0641\u064a \u064a\u0648\u0645 {day} \u0627\u0644\u0645\u0648\u0627\u0641\u0642 {d.strftime('%d-%m-%Y')}"

    # ==============================
    # FORMAT MONEY (for templates)
    # ==============================
    def get_formatted_amount(self):
        return f"{self.amount_total:,.2f} {self.currency_id.name or ''}"

    def get_end_date_arabic(self):
        if not self.end_date:
            return ""
        days = {
            'Sunday': '\u0627\u0644\u0627\u062d\u062f', 'Monday': '\u0627\u0644\u0627\u062b\u0646\u064a\u0646',
            'Tuesday': '\u0627\u0644\u062b\u0644\u0627\u062b\u0627\u0621', 'Wednesday': '\u0627\u0644\u0627\u0631\u0628\u0639\u0627\u0621',
            'Thursday': '\u0627\u0644\u062e\u0645\u064a\u0633', 'Friday': '\u0627\u0644\u062c\u0645\u0639\u0629',
            'Saturday': '\u0627\u0644\u0633\u0628\u062a'
        }
        day = days.get(self.end_date.strftime('%A'), self.end_date.strftime('%A'))
        return f"{day} \u0627\u0644\u0645\u0648\u0627\u0641\u0642 {self.end_date.strftime('%d-%m-%Y')}"

    # ==============================
    # DASHBOARD DATA
    # ==============================
    @api.model
    def get_dashboard_data(self):
        """Get data for the contract dashboard"""
        today = fields.Date.today()
        contracts = self.search([])
        
        total_contracts = len(contracts)
        draft_contracts = len(contracts.filtered(lambda c: c.state == 'draft'))
        active_contracts = len(contracts.filtered(lambda c: c.state in ('confirmed', 'financial_approved', 'legal_approved', 'finished') and not c.is_expired))
        expired_contracts = len(contracts.filtered(lambda c: c.is_expired))
        cancelled_contracts = len(contracts.filtered(lambda c: c.state == 'cancelled'))
        
        total_value = sum(contracts.mapped('amount_total'))
        active_value = sum(contracts.filtered(lambda c: c.state in ('confirmed', 'financial_approved', 'legal_approved', 'finished') and not c.is_expired).mapped('amount_total'))
        
        # Expiring soon (next 30 days)
        expiring_soon = len(contracts.filtered(lambda c: c.can_be_renewed and not c.is_expired))
        
        # Contracts created this month
        month_start = today.replace(day=1)
        this_month = len(contracts.filtered(lambda c: c.create_date and c.create_date.date() >= month_start))
        
        # Total invoiced vs remaining
        total_invoiced = sum(contracts.mapped('invoiced_amount'))
        total_remaining = sum(contracts.mapped('remaining_amount'))
        
        # Overdue installments
        overdue_installments = self.env['contract.payment.schedule'].search_count([
            ('state', '=', 'pending'),
            ('due_date', '<', today),
        ])
        
        return {
            'total_contracts': total_contracts,
            'draft_contracts': draft_contracts,
            'active_contracts': active_contracts,
            'expired_contracts': expired_contracts,
            'cancelled_contracts': cancelled_contracts,
            'total_value': total_value,
            'active_value': active_value,
            'expiring_soon': expiring_soon,
            'this_month': this_month,
            'total_invoiced': total_invoiced,
            'total_remaining': total_remaining,
            'overdue_installments': overdue_installments,
        }

    @api.model
    def get_contracts_by_state_data(self):
        """Get contract counts by state for pie chart"""
        self._cr.execute("""
            SELECT state, COUNT(*) as count
            FROM sale_contract
            GROUP BY state
            ORDER BY count DESC
        """)
        return self._cr.dictfetchall()

    @api.model
    def get_contracts_by_month_data(self):
        """Get contract counts per month for bar chart (last 12 months)"""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        today = fields.Date.today()
        result = []
        for i in range(11, -1, -1):
            month_start = (today - relativedelta(months=i)).replace(day=1)
            month_end = (month_start + relativedelta(months=1))
            count = self.search_count([
                ('create_date', '>=', month_start.strftime('%Y-%m-%d')),
                ('create_date', '<', month_end.strftime('%Y-%m-%d')),
            ])
            month_name = month_start.strftime('%b %Y')
            result.append({'month': month_name, 'count': count})
        return result

    @api.model
    def get_top_partners_data(self):
        """Get top partners by contract value"""
        self._cr.execute("""
            SELECT rp.name, SUM(sc.amount_total) as total
            FROM sale_contract sc
            JOIN res_partner rp ON sc.partner_id = rp.id
            WHERE sc.state NOT IN ('draft', 'cancelled')
            GROUP BY rp.name
            ORDER BY total DESC
            LIMIT 10
        """)
        return self._cr.dictfetchall()

    @api.model
    def get_expiry_timeline_data(self):
        """Get contracts grouped by expiry period"""
        today = fields.Date.today()
        from datetime import timedelta
        
        periods = {
            'expired': self.search_count([('end_date', '<', today)]),
            'next_7_days': self.search_count([
                ('end_date', '>=', today),
                ('end_date', '<=', today + timedelta(days=7)),
            ]),
            'next_30_days': self.search_count([
                ('end_date', '>', today + timedelta(days=7)),
                ('end_date', '<=', today + timedelta(days=30)),
            ]),
            'next_90_days': self.search_count([
                ('end_date', '>', today + timedelta(days=30)),
                ('end_date', '<=', today + timedelta(days=90)),
            ]),
            'more_than_90': self.search_count([
                ('end_date', '>', today + timedelta(days=90)),
            ]),
        }
        return periods

    # ==============================
    # DELETE RULE
    # ==============================
    def unlink(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(
                    "You can only delete contracts in Draft state."
                )
        return super(SaleContract, self).unlink()
