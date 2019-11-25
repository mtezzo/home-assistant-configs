"""Synology Surveillance Station."""

__version__ = '1.0.1'

import logging
from requests.exceptions import RequestException
import voluptuous as vol
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_VERIFY_SSL,
    CONF_TIMEOUT
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5
DOMAIN = 'surveillance_station'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_URL): cv.url,
        vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int
     })),
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up the Synology Surveillance Station component."""

    # Get values from config
    conf = config[DOMAIN]
    verify_ssl = conf.get(CONF_VERIFY_SSL)
    timeout = conf.get(CONF_TIMEOUT)

    try:
        from synology.surveillance_station import SurveillanceStation

        surveillance = SurveillanceStation(
            conf.get(CONF_URL),
            conf.get(CONF_USERNAME),
            conf.get(CONF_PASSWORD),
            verify_ssl=verify_ssl,
            timeout=timeout,
        )
    except (RequestException, ValueError):
        _LOGGER.exception("Error when initializing SurveillanceStation")
        return False

    hass.states.set('surveillance_station.home_mode', "home" if surveillance.get_home_mode_status() == "true" else "away")

    def handle_set_home_mode(call):
        """Handle the service call."""

        mode = call.data.get('home_mode', 'away').lower()

        # Set the Home Mode
        if surveillance.set_home_mode(True if mode == 'home' else False):
            _LOGGER.info('Successfully set mode to: %s', mode)
        else:
            _LOGGER.error('Failed set mode to: %s', mode)

        hass.states.set('surveillance_station.home_mode', mode)

    hass.services.register(DOMAIN, 'set_home_mode', handle_set_home_mode)

    # Return boolean to indicate that initialization was successful.
    return True
