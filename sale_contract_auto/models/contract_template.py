from odoo import models, fields, api


class ContractTemplate(models.Model):
    _name = 'contract.template'
    _description = 'Contract Terms Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    content = fields.Html(string='Agreement Terms')
    clause_ids = fields.Many2many(
        'contract.clause',
        'contract_template_clause_rel',
        'template_id', 'clause_id',
        string='Clauses'
    )

    def _render_template(self, text, model, res_id):
        """Replace placeholders with actual values"""
        if not text:
            return text
        try:
            record = self.env[model].browse(res_id)
            if not record.exists():
                return text

            placeholders = {
                '{{company_name}}': record.first_party_name or '',
                '{{partner_name}}': record.partner_id.name or '',
                '{{contract_name}}': record.name or '',
                '{{contract_date}}': record.contract_date.strftime('%Y-%m-%d') if record.contract_date else '',
                '{{start_date}}': record.start_date.strftime('%Y-%m-%d') if record.start_date else '',
                '{{end_date}}': record.end_date.strftime('%Y-%m-%d') if record.end_date else '',
                '{{amount_total}}': f"{record.amount_total:,.2f}" or '0.00',
                '{{currency}}': record.currency_id.name or '',
                '{{company_registry}}': record.first_party_registry or '',
                '{{company_address}}': record.first_party_address or '',
                '{{partner_address}}': record.second_party_address or '',
                '{{partner_id_card}}': record.second_party_id_card or '',
                '{{arabic_date}}': record.get_arabic_date() or '',
                '{{end_date_arabic}}': record.get_end_date_arabic() or '',
                '{{formatted_amount}}': record.get_formatted_amount() or '',
            }

            result = text
            for key, value in placeholders.items():
                result = result.replace(key, str(value))

            return result
        except Exception:
            return text
