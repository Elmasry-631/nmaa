from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    investment_club_access = fields.Boolean(
        string="Investment Club Access",
        compute="_compute_investment_club_access",
        inverse="_inverse_investment_club_access",
    )

    def _get_investment_club_group(self):
        return self.env.ref(
            "investment_club.group_investment_access",
            raise_if_not_found=False,
        )

    @api.depends("groups_id")
    def _compute_investment_club_access(self):
        group = self._get_investment_club_group()
        if not group:
            for user in self:
                user.investment_club_access = False
            return
        for user in self:
            user.investment_club_access = group in user.groups_id

    def _inverse_investment_club_access(self):
        group = self._get_investment_club_group()
        if not group:
            return
        for user in self:
            if user.investment_club_access:
                user.write({"groups_id": [(4, group.id)]})
            else:
                user.write({"groups_id": [(3, group.id)]})

