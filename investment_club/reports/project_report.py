# investment_club/reports/project_report.py
from odoo import models, api, fields


class ProjectSummaryReport(models.AbstractModel):
    _name = 'report.investment_club.project_summary'
    _description = 'Project Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        projects = self.env['investment.project'].browse(docids)
        
        report_data = []
        grand_total = {
            'invested': 0,
            'investors': 0,
            'branches': 0,
            'monthly_return': 0,
            'annual_return': 0,
        }
        
        for project in projects:
            # الاستثمارات النشطة
            investments = self.env['investment.subscription'].search([
                ('project_id', '=', project.id),
                ('state', '=', 'active')
            ])
            
            total_invested = sum(inv.amount for inv in investments)
            investor_count = len(investments)
            branch_count = (investor_count + project.investors_per_branch - 1) // project.investors_per_branch if project.investors_per_branch else 0
            monthly_return = sum(inv.expected_monthly_return for inv in investments)
            
            report_data.append({
                'name': project.name,
                'code': project.code,
                'club': project.club_id.name,
                'analytic_account': project.analytic_account_id.name,
                'share_value': project.share_value,
                'target_investors': f"{project.expected_customers_min} - {project.expected_customers_max}",
                'actual_investors': investor_count,
                'branches': branch_count,
                'total_invested': total_invested,
                'monthly_return': monthly_return,
                'annual_return': monthly_return * 12,
                'roi': (monthly_return * 12 / total_invested * 100) if total_invested else 0,
            })
            
            grand_total['invested'] += total_invested
            grand_total['investors'] += investor_count
            grand_total['branches'] += branch_count
            grand_total['monthly_return'] += monthly_return
            grand_total['annual_return'] += monthly_return * 12
        
        return {
            'docs': projects,
            'data': report_data,
            'grand_total': grand_total,
            'date': fields.Date.today(),
        }