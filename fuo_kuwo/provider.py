import logging

from fuocore.provider import AbstractProvider

from . import __identifier__, __alias__
from .api import KuwoApi

logger = logging.getLogger(__name__)


class KuwoProvider(AbstractProvider):
    api: KuwoApi

    def __init__(self):
        super().__init__()
        self.api = KuwoApi()

    @property
    def name(self) -> str:
        return __alias__

    @property
    def identifier(self) -> str:
        return __identifier__


provider = KuwoProvider()

from .models import search
provider.search = search
