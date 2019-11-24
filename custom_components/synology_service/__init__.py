"""Synology Surveillance Station Service."""

__version__ = '1.0.0'

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from requests import get

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'synology_service'

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_URL = 'url'

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

    def handle_set_home(call):
        """Handle the service call."""

        # Create New SynoService
        synology = SynoService(url)

        # If we successfully login
        if synology.login(username, password):
            # Set the Home Mode
            synology.set_home(call.data.get('home', False))

        hass.states.set('synology_service.home', False)

    hass.services.register(DOMAIN, 'set_home', handle_set_home)

    # Return boolean to indicate that initialization was successful.
    return True

class SynoService():
    def __init__(self, url):
        self.url = url + '/webapi/'
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

        result = get(self.url + 'auth.cgi', params=loginParams)
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

        result = get(self.url + 'entry.cgi', params=modeParams)
        data = result.json()

        if result and data["success"] is True:
            _LOGGER.info('Successfully set mode to: %s', 'home' if mode else 'away')
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
            result = get(self.url + 'auth.cgi', params=logoutParams)
            data = result.json()

            if result and data["success"] is True:
                _LOGGER.debug('Successfully logged out of Synology.')
            else:
                _LOGGER.error('Failed to logout of Synology', self.url)
