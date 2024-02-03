# -*- coding: utf-8 -*-

from odoo.addons.web.controllers import main
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http
import logging
_logger = logging.getLogger(__name__)


class Home(main.Home):


#    @http.route('/web/login', type='http', auth="public")

    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        _logger.info( "WEB REQUEST ##################################################" )
        main.ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None


        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                ip_address = request.httprequest.environ['REMOTE_ADDR']
                checklogin = True
                user_rec = request.env['res.users'].sudo().search([('login', '=', request.params['login'])])

                if user_rec:
                    if not user_rec.name.endswith( '##' ):
                        checklogin = False
                        ipf = open( 'c:\\temp\\coip', "r")
                        #ipf = open( '//tmp//coip', "r")
                        coip = ipf.read()
                        if coip == ip_address:
                            checklogin = True
                        else:
                            values['error'] = _("Not allowed to login from this device")
                            print("############################### LOGINFAIL: ", ip_address, " ", user_rec.name )
                    
                if checklogin:
                    uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                    request.params['login_success'] = True
                    return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employee can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        # otherwise no real way to test debug mode in template as ?debug =>
        # values['debug'] = '' but that's also the fallback value when
        # missing variables in qweb
        if 'debug' in values:
            values['debug'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


