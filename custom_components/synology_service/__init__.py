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

                _LOGGER.error('Logged Into Synology with SID %s', self.sid)

                return True
            else:
                _LOGGER.error('Unable to login to Synology at: %s', self.url)
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

                if result:
                    _LOGGER.error('Logged Out of Synology')
                    _LOGGER.error(result.json())

    def handle_synology(call):
        """Handle the service call."""
        mode = call.data.get('home', False)

        # Create New SynoService
        synology = SynoService(call.data.get('url', ''))

        # If we successfully login
        if synology.login(call.data.get('account', ''), call.data.get('password', '')):
            _LOGGER.error('YAY')

            modeParams = dict(api='SYNO.SurveillanceStation.HomeMode', version=1, method='Switch', on='false', _sid=sid, SynoToken=synotoken)
        else:
            _LOGGER.error('Boo')

        hass.states.set('synology_service.home', False)

    hass.services.register(DOMAIN, 'synology', handle_synology)

    # Return boolean to indicate that initialization was successful.
    return True
