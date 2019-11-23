from requests import get

URL = data.get('nas_url') + '/webapi/auth.cgi'

loginParams = dict(api='SYNO.API.Auth', method='Login', version=6, account=data.get('nas_username'), passwd=data.get('nas_password'), session='SurveillanceStation', format='sid', enable_syno_token='yes')

r = get(URL, params=loginParams)

data = r.json()

print(data)

modeParams = dict(api='SYNO.SurveillanceStation.HomeMode', version=1, method='Switch', on='false', _sid='', SynoToken='')



logoutParams = dict(api='SYNO.API.Auth', method='Logout', version=1, session='SurveillanceStation', _sid='', SynoToken='')

#r = get(URL, params=logoutParams)
