"""Synology Surveillance Station Service."""

from requests import get

__version__ = '1.0.0'

DOMAIN = 'synology_service'

def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    def handle_synology(call):
        """Handle the service call."""
        url = call.data.get('url', '') + '/webapi/auth.cgi'
        mode = call.data.get('home', False)

        loginParams = dict(api='SYNO.API.Auth', method='Login', version=6, account=call.data.get('account', ''), passwd=call.data.get('password', ''), session='SurveillanceStation', format='sid', enable_syno_token='yes')

        r = get(url, params=loginParams)

        data = r.json()

        print(data)

        hass.states.set('synology_service.home', False)

    hass.services.register(DOMAIN, 'synology', handle_synology)

    # Return boolean to indicate that initialization was successful.
    return True
