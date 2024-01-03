import json
import os

from feeluown.consts import DATA_DIR
from feeluown.library import BriefUserModel
from feeluown.gui.widgets import CookiesLoginDialog
from feeluown.gui.widgets.login import InvalidCookies
from feeluown.utils import aio
from feeluown.gui.provider_ui import AbstractProviderUi

from . import __identifier__, __alias__
from .provider import provider

USER_INFO_FILE = DATA_DIR + '/kuwo_music_user_session.json'


class ProviderUi(AbstractProviderUi):
    def __init__(self, app):
        self._app = app

    @property
    def provider(self):
        return provider

    def get_colorful_svg(self) -> str:
        return os.path.join(os.path.dirname(__file__), 'assets', 'icon.svg')

    def login_or_go_home(self):
        if provider.user is None:
            self._dialog = dialog = LoginDialog()
            dialog.login_succeed.connect(lambda: aio.run_afn(self.load_user))
            dialog.show()
            dialog.autologin()
        else:
            aio.run_afn(self.load_user)

    async def load_user(self):
        self._app.ui.left_panel.playlists_con.show()
        self._app.pl_uimgr.clear()
        user_playlists = await aio.run_fn(provider.current_user_playlists)
        self._app.pl_uimgr.add(user_playlists)


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
            user = BriefUserModel(source=__identifier__, identifier=userid)
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
