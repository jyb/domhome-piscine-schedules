#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :


"""
    creation des schedules piscine :
fonction de la temperature piscine (idealement une moyenne de la veille ou la meme date l'enne d'avant, TBC),
on cree un schedule pour :
   - la pompe et la vitesse
   - la pompe de Chlore liquide
   - le polaris

Selon la tremperature piscine, on a 8 schedules differents

Temp piscine         horaires start (B) et stop (E) d'apres schema Cathie
                 00:00  03:00  04:00  06:00  07:00     08:00      11:30       12:00  14:00      14:30       20:00    22:00
Temp < 10°C                     B.V1   E.V1
10 < Temp < 12           B.V1    V1     V1    E.V1
12 < Temp < 16    B.V1    V1     E.V1                             B.V4        B.Pol  E.Pol      E.V4    
16 < Temp < 24                                         B.V2     E.V2-B.V4     B.Pol  E.Pol     E.V4-B.V3     E.V3
24 < Temp < 27                                         B.V2     E.V2-B.V4     B.Pol  E.Pol     E.V4-B.V3             E.V3
27 < Temp < 30                  B.V1                E.V1-B.V2   E.V2-B.V4     B.Pol  E.Pol     E.V4-B.V3             E.V3

NOTA: 
 - verifier que la pompe marche quand on active le Polaris, ou la pompe


Ex de recup Temp piscine via Domoticz :
TEMP_PISCINE=$(curl -u "bougon:jeyvbu55" -s  "http://dgbaley:8080/json.htm?type=devices&rid=108" | jq '.result[0].Data' | sed -e 's/"//g' | awk '{print $1}') ; echo "$TEMP_PISCINE" 


https://pypi.org/project/urllib3/
https://urllib3.readthedocs.io/en/stable/reference/index.html


"""
import json
import urllib.request, urllib.error, urllib.parse
import base64
import urllib3
import pprint


## domoticzurl = 'http://bougon:jeyvbu55@dgbaley:8080/json.htm?type=devices&rid=108'
uclair = 'bougon'
pclair = 'jeyvbu55'

u=base64.b64encode(uclair.encode('ascii'))
p=base64.b64encode(pclair.encode('ascii'))


## domoticzurl = ('http://dgbaley:8080/json.htm?username={}&password={}?type=devices&rid=108'.format (u, p))

## domoticzurl = ('http://dgbaley:8080/json.htm?username={}&password={}?type=devices&rid=108'.format (uclair, pclair))

domoticzurl = ('http://dgbaley:8080/json.htm?username={}&password={}?type=devices&rid=108'.format (u, p))

print("Call : {}".format(domoticzurl))


## ==============================================================
## Schedule : objet qui represente un schedule parmiceux possibles
## TODO: APRES !!!!
class Schedule:
    "Schedule des services piscine (pompe principale, pompe chlore, polaris)"
    def __init__(self, heure, minute, objet, action):
        self.heure = heure
    def genere_crontab(self, crontab1):
        crontab1 = "30 12 * * *  /tmp/script1.sh"
        return(crontab1)
## ==============================================================





def domoticzrequest (url):
    """
    request = urllib.request.Request(url)
    base64string = base64.b64encode(('%s:%s' % (uclair, pclair)).encode('ascii'))
    request.add_header("Authorization", "Basic %s" % base64string)   
    response = urllib.request.urlopen(request)
    return response.read()
    """

    http = urllib3.PoolManager()
    ## headers={'Content-Type': 'application/json'})
    myHeaders = urllib3.util.make_headers(basic_auth='%s:%s' % (uclair, pclair))
    resp = http.request('GET', 'http://dgbaley:8080/json.htm?type=devices&rid=108', headers=myHeaders)
    print(resp)
    print(resp.status)
    res_body = resp.data
    print(res_body)
    datajson = json.loads(res_body.decode('utf-8'))
    print(type(datajson))
    pprint.pprint(datajson)
    print(type(datajson['result'][0]))
    temp1 = (datajson['result'][0]['Data'])
    ## recoit '17.4 C'

    temptab = temp1.split()
    temp = float(temptab[0])
    print("Temp : {}".format(temp))



"""
json_object = json.loads(domoticzrequest(domoticzurl))
if json_object["status"] == "OK":
    print(json_object["version"])
"""
domoticzrequest(domoticzurl)





