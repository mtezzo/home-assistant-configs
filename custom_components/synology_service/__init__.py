"""Synology Surveillance Station Service."""

import logging
from requests import get

__version__ = '1.0.0'

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'synology_service'

def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    class SynoService():
        def __init__(self, url):
            self.url = url + '/webapi/auth.cgi'
            self.sid = None
            self.synotoken = None

        def login(self, username, password):

            loginParams = dict(
                api = 'SYNO.API.Auth',
                method = 'Login',
                version = 6,
                account = username,
                passwd = password,
                session = 'SurveillanceStation',
                format = 'sid',
                enable_syno_token = 'yes'
            )

            result = get(self.url, params=loginParams)
            data = result.json()

            if result and data["success"] is True:
                self.sid = data["data"]["sid"]
                self.synotoken = data["data"]["synotoken"]

                _LOGGER.debug('Successfully logged into Synology at: %s', self.url)
                return True
            else:
                _LOGGER.error('Failed to login to Synology at: %s', self.url)
                return False

        def set_home(self, mode):
            # Fail if not logged in
            if self.sid is None:
                return False

            modeParams = dict(
                api = 'SYNO.SurveillanceStation.HomeMode',
                version = 1,
                method = 'Switch',
                on = 'true' if mode else 'false',
                _sid = self.sid,
                SynoToken = self.synotoken
            )

            result = get(self.url, params=modeParams)
            data = result.json()

            if result and data["success"] is True:
                _LOGGER.error('Successfully set mode to: %s', 'home' if mode else 'away')
                return True
            else:
                _LOGGER.error('Failed set mode to: %s', 'home' if mode else 'away')
                return False

        def __del__(self):
            logoutParams = dict(
                api = 'SYNO.API.Auth',
                method = 'Logout',
                version = 1,
                session = 'SurveillanceStation',
                _sid = self.sid,
                SynoToken = self.synotoken
            )

            if self.sid is not None:
                result = get(self.url, params=logoutParams)
                data = result.json()

                if result and data["success"] is True:
                    _LOGGER.debug('Successfully logged out of Synology.')
                else:
                    _LOGGER.error('Failed to logout of Synology', self.url)

    def handle_set_home(call):
        """Handle the service call."""

        # Create New SynoService
        synology = SynoService(call.data.get('url', ''))

        # If we successfully login
        if synology.login(call.data.get('account', ''), call.data.get('password', '')):
            # Set the Home Mode
            synology.set_home(call.data.get('home', False))

        hass.states.set('synology_service.home', False)

    hass.services.register(DOMAIN, 'set_home', handle_set_home)

    # Return boolean to indicate that initialization was successful.
    return True
