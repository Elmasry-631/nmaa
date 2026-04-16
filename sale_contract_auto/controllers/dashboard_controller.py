from odoo import http
from odoo.http import request


class ContractDashboard(http.Controller):

    @http.route('/contracts/dashboard', type='http', auth='user')
    def dashboard(self, **kwargs):
        """Render the contract dashboard page"""
        contract_model = request.env['sale.contract']

        dashboard_data = contract_model.get_dashboard_data()
        by_state = contract_model.get_contracts_by_state_data()
        by_month = contract_model.get_contracts_by_month_data()
        top_partners = contract_model.get_top_partners_data()
        expiry_timeline = contract_model.get_expiry_timeline_data()

        return request.render('sale_contract_auto.contract_dashboard_template', {
            'data': dashboard_data,
            'by_state': by_state,
            'by_month': by_month,
            'top_partners': top_partners,
            'expiry_timeline': expiry_timeline,
        })
