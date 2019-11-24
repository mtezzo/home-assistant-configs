"""Synology Surveillance Station."""

__version__ = '1.0.0'

import logging
import voluptuous as vol
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_URL)
import homeassistant.helpers.config_validation as cv
from requests import get

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'surveillance_station'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_URL): cv.url
     })),
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up the Synology Surveillance Station component."""

    conf = config[DOMAIN]

    username = conf.get(CONF_USERNAME)
    password = conf.get(CONF_PASSWORD)
    url = conf.get(CONF_URL)

    def handle_set_home_mode(call):
        """Handle the service call."""

        # Create New SynoService
        synology = SynoService(url)

        # If we successfully login
        if synology.login(username, password):
            mode = call.data.get('home_mode', 'away').lower()

            # Set the Home Mode
            if synology.set_home(True if mode == 'home' else False):
                _LOGGER.info('Successfully set mode to: %s', mode)
            else:
                _LOGGER.error('Failed set mode to: %s', mode)

        hass.states.set('surveillance_station.home_mode', mode)

    hass.services.register(DOMAIN, 'set_home_mode', handle_set_home_mode)

    # Return boolean to indicate that initialization was successful.
    return True

class SynoService():
    def __init__(self, url):
        self.url = url + '/webapi/'
        self.sid = None
        self.synotoken = None

    def login(self, username, password):
        """Login to synology API"""

        result = get(
            self.url + 'auth.cgi',
            params = dict(
                api = 'SYNO.API.Auth',
                method = 'Login',
                version = 6,
                account = username,
                passwd = password,
                session = 'SurveillanceStation',
                format = 'sid',
                enable_syno_token = 'yes'
            )
        )

        # Get JSON data
        data = result.json()

        if result and data["success"] is True:
            self.sid = data["data"]["sid"]
            self.synotoken = data["data"]["synotoken"]

            _LOGGER.debug('Successfully logged into Synology at: %s', self.url)
            return True
        else:
            _LOGGER.error('Failed to login to Synology at: %s', self.url)
            return False

    def set_home(self, is_home):
        """ Set home mode of surveillance station"""

        # Fail if not logged in
        if self.sid is None:
            return False

        result = get(
            self.url + 'entry.cgi',
            params = dict(
                api = 'SYNO.SurveillanceStation.HomeMode',
                version = 1,
                method = 'Switch',
                on = 'true' if is_home else 'false',
                _sid = self.sid,
                SynoToken = self.synotoken
            )
        )

        return (result and result.json()["success"] is True)

    def __del__(self):
        """Logout automatically on descruction if we're still logged in"""

        if self.sid is not None:
            result = get(
                self.url + 'auth.cgi',
                params = dict(
                    api = 'SYNO.API.Auth',
                    method = 'Logout',
                    version = 1,
                    session = 'SurveillanceStation',
                    _sid = self.sid,
                    SynoToken = self.synotoken
                )
            )

            if result and result.json()["success"] is True:
                _LOGGER.debug('Successfully logged out of Synology.')
            else:
                _LOGGER.error('Failed to logout of Synology: %s', self.url)
