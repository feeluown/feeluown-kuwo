import json
import os
from pathlib import Path

from feeluown.consts import DATA_DIR
from feeluown.gui.widgets import CookiesLoginDialog
from feeluown.gui.widgets.login import InvalidCookies
from feeluown.uimodels.provider import ProviderUiManager
from feeluown.utils import aio

from . import __alias__
from .provider import provider

USER_INFO_FILE = DATA_DIR + '/kuwo_music_user_session.json'


class KuwoUiManager:
    def __init__(self, app):
        self._app = app
        self._pvd_uimgr: ProviderUiManager = app.pvd_uimgr
        self._pvd_item = self._pvd_uimgr.create_item(
            name='kuwo',
            text=__alias__,
            symbol='♫ ',
            desc='点击登录',
            colorful_svg=str(Path(__file__).resolve().parent / 'assets' / 'icon.svg'))
        self._pvd_item.clicked.connect(self.login_or_show)
        self._pvd_uimgr.add_item(self._pvd_item)

    def login_or_show(self):
        if provider.user is None:
            dialog = LoginDialog()
            dialog.login_succeed.connect(self.load_user)
            dialog.show()
            dialog.autologin()
        else:
            self.load_user()

    def load_user(self):
        user = provider.user
        self._app.ui.left_panel.my_music_con.hide()
        self._app.ui.left_panel.playlists_con.show()
        self._app.pl_uimgr.clear()
        self._app.pl_uimgr.add(user.playlists)
        self._pvd_item.text = f'{__alias__} - 已登录'


class LoginDialog(CookiesLoginDialog):

    def setup_user(self, user):
        provider.user = user

    async def user_from_cookies(self, cookies):
        if not cookies:  # is None or empty
            raise InvalidCookies('empty cookies')

        userid, sid = provider.api.get_user_from_cookies(cookies)
        if not userid:
            raise InvalidCookies("can't extract user info from cookies")

        provider.api.set_cookies(cookies)
        # try to extract current user
        try:
            user = await aio.run_in_executor(None, provider.User.get, userid)
        except Exception:
            provider.api.set_cookies(None)
            raise InvalidCookies('get user info with cookies failed, expired cookies?')
        else:
            return user

    def load_user_cookies(self):
        if os.path.exists(USER_INFO_FILE):
            # if the file is broken, just raise error
            with open(USER_INFO_FILE) as f:
                return json.load(f).get('cookies', None)

    def dump_user_cookies(self, user, cookies):
        js = {
            'identifier': user.identifier,
            'name': user.name,
            'cookies': cookies
        }
        with open(USER_INFO_FILE, 'w') as f:
            json.dump(js, f, indent=2)
