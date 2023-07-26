import logging

import Assets
import Auth
import Comments
import Incidents
import Settings
import Tenants
import HttpClient

from .organizations import Organizations
from .schedules import Schedules

logger = logging.getLogger()


class MDRRestAPi(HttpClient):
    _WRAPPERS = [
        Auth, Assets, Comments, Tenants, Incidents, Schedules, Organizations, Settings
    ]

    def __init__(self, *args, **kwargs):
        super(MDRRestAPi, self).__init__(*args, **kwargs)

        self.auth = None
        self.assets = None
        self.tenants = None
        self.incidents = None
        self.schedules = None
        self.sessions = None
        self.organizations = None
        self.settings = None
        self.comments = None

        for e in self._WRAPPERS:
            attr_name = e.__name__.lower()
            setattr(self, attr_name, e(self))
