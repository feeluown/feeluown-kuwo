# *-- coding: utf-8 --*
__alias__ = '酷我音乐'
__feeluown_version__ = '3.1'
__version__ = '0.1.1'
__desc__ = __alias__
__identifier__ = 'kuwo'

from feeluown.app import App

from .provider import provider


def enable(app: App):
    global ui_mgr
    app.library.register(provider)
    if app.mode & App.GuiMode:
        from .ui import ProviderUi

        provider_ui = ProviderUi(app)
        app.pvd_ui_mgr.register(provider_ui)


def disable(app: App):
    app.library.deregister(provider)
    if app.mode & App.GuiMode:
        app.providers.remove(provider.identifier)
