import urllib
import urllib.parse
import urllib.request
import simplejson

googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'

def get_coordinates(query, from_sensor=False):
    query = query.encode('utf-8')
    params = {
        'address': query,
        'sensor': "true" if from_sensor else "false"
    }
    url = googleGeocodeUrl + urllib.parse.urlencode(params)
    json_response = urllib.request.urlopen(url)
    response = simplejson.loads(json_response.read())
    if response['results']:
        location = response['results'][0]['geometry']['location']
        latitude, longitude = location['lat'], location['lng']
        print(query, latitude, longitude)
    else:
        latitude, longitude = None, None
        print(query, "<no results>")
    return latitude, longitude

print(get_coordinates('Deatsville 3.4 NW, AL'))