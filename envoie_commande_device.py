#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :


"""
    envoie_commande_device.py : envoie des commandes a certains devices (dispositifs)
    JYB - 2023/04/10

Utilise par les commandes envoyees aux periph via crontab
 - envoie a Domoticz via REST API des ordres tels que On, Off
 - liste des devices connue (pompes, polaris, eventuellement lumieres/switches cameras)
 - dans le cas de la pompe principale, on n'a pas de connexion/pilotage, donc il faut  le planning dans Domoticz est    

Lancement : 
$ python3 envoie_commande_device.py
Pas besoin de venv python, pas de modules particuliers


Ex d'envoi de la commande "On" a la pompe Chlore via Domoticz :
curl -XGET -u "bougon:passwd"  "http://dgbaley:8080/json.htm?type=command&param=switchlight&idx=414&switchcmd=On"
{
	"status" : "OK",
	"title" : "SwitchLight"
}

Ex de recup Temp piscine via Domoticz :
TEMP_PISCINE=$(curl -u "bougon:passwd" -s  "http://dgbaley:8080/json.htm?type=devices&rid=108" | jq '.result[0].Data' | sed -e 's/"//g' | awk '{print $1}') ; echo "$TEMP_PISCINE" 
Ex de mise en route de la pompe de chlore liquide

https://pypi.org/project/urllib3/
https://urllib3.readthedocs.io/en/stable/reference/index.html


"""
import os
import time
import datetime
import sys
import json
import base64
import urllib3
import pprint
import inspect
import logging
import traceback


list_dict_devices = [
    {
        "nom": "polaris",
        "idx": 999,
        "desc": "Pompe surpresseur du Robot Polaris via relai gladia 3",
    },
    {
        "nom": "chlore",
        "idx": 414,
        "desc": "Pompe chlore liquide (ex OXAR) via relai gladia 2",
    },
    {
        "nom": "pompeV1",
        "idx": 1440,
        "desc": "Pompe Vitesse 1 (pas de liaison, verifier planning Domoticz du device/switch)",
    },
    {
        "nom": "pompeV2",
        "idx": 1441,
        "desc": "Pompe Vitesse 2 (pas de liaison, verifier planning Domoticz du device/switch)",
    },
    {
        "nom": "pompeV3",
        "idx": 1442,
        "desc": "Pompe Vitesse 3 (pas de liaison, verifier planning Domoticz du device/switch)",
    },
    {
        "nom": "pompeV4",
        "idx": 1440,
        "desc": "Pompe Vitesse 4 (pas de liaison, verifier planning Domoticz du device/switch)",
    },

    
]


## -+- CONSTANTES -+-
## mode_debug = False
## mode_debug = True
mode_debug = False

## Codes d'erreurs
code_ok = 0
code_err = 1

g_compteur_messages = 0



## ==============================================================
## MonEnv : objet qui garde en RAM qqs variables d'env

class MonEnv:
    "garde en RAM qqs variables d'env"
    ## udom
    ## pdom
    ## 
    ## repscripts

    def __init__(self, ):
        self.udom = os.environ.get('SCHED_DOMOTICZ_USER')
        ## pprint.pprint(self.udom)
        if self.udom == None:
            arret_msg("Variable d'environnement 'SCHED_DOMOTICZ_USER' non renseignee. Stop.")
        self.pdom = os.environ.get('SCHED_DOMOTICZ_PASSWD')
        if self.pdom == None:
            arret_msg("Variable d'environnement 'SCHED_DOMOTICZ_PASSWD' non renseignee. Stop.")
        self.repscripts = os.environ.get('SCHED_SCRIPTS_DIR')
        if self.repscripts == None:
            arret_msg("Variable d'environnement 'SCHED_SCRIPTS_DIR' non renseignee. Stop.")
        

    def get_user(self):
        return(self.udom)
    def get_pwd(self):
        return(self.pdom)
    def get_scripts_dir(self):
        return(self.repscripts)
    

## ==============================================================



"""
  Au depart on a une liste de schedules ; chacun est un tableau de dict ;
  chaque dict est un front montant ou descendant applique a un objet a une heure/minutes donnes
  donne ici en hard code, il y a 2 fonctions de chargement ou creation d'un JSON, donc on peut partir d'un JSON externe si besoin
"""
schedule = [
   {
    "type": "hiver",
    "desc": "temp inf a 10°C", 
    "duree_filtration_totale": "2",
    "temp_min": "-100",
    "temp_max": "10",
    "scheds": [
        { "heure": "04", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "start"
            },
        { "heure": "06", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "stop"
            },
    ],
   },
   {
    "type": "type2",
    "desc": "temp entre 10°C et 12°C", 
    "duree_filtration_totale": "4",
    "temp_min": "10",
    "temp_max": "12",
    "scheds": [
        { "heure": "03", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "start"
            },
        { "heure": "07", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "stop"
            },
    ],
   },
   {
    "type": "type3",
    "desc": "temp entre 12°C et 16°C", 
    "duree_filtration_totale": "7",
    "temp_min": "12",
    "temp_max": "16",
    "scheds": [
        { "heure": "00", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "start"
            },
        { "heure": "04", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "stop"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "stop"
            },
        { "heure": "12", 
            "minutes": "00",
            "objet": "polaris",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "00",
            "objet": "polaris",
            "action": "stop"
            },

    ],
   },
   {
    "type": "type4",
    "desc": "temp entre 16°C et 24°C", 
    "duree_filtration_totale": "8 a 12",
    "temp_min": "16",
    "temp_max": "24",
    "scheds": [
        { "heure": "08", 
            "minutes": "00",
            "objet": "pompeV2",
            "action": "start"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV2",
            "action": "stop"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "stop"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV3",
            "action": "start"
            },
        { "heure": "20", 
            "minutes": "00",
            "objet": "pompeV3",
            "action": "stop"
            },
        { "heure": "12", 
            "minutes": "00",
            "objet": "polaris",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "00",
            "objet": "polaris",
            "action": "stop"
            },
    ],
   },
   {
    "type": "type5",
    "desc": "temp entre 24°C et 27°C", 
    "duree_filtration_totale": "10 a 14",
    "temp_min": "24",
    "temp_max": "27",
    "scheds": [
        { "heure": "08", 
            "minutes": "00",
            "objet": "pompeV2",
            "action": "start"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV2",
            "action": "stop"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "stop"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV3",
            "action": "start"
            },
        { "heure": "22", 
            "minutes": "00",
            "objet": "pompeV3",
            "action": "stop"
            },
        { "heure": "12", 
            "minutes": "00",
            "objet": "polaris",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "00",
            "objet": "polaris",
            "action": "stop"
            },
    ],
   },
   {
    "type": "type6",
    "desc": "temp entre 27°C et 30°C", 
    "duree_filtration_totale": "15 a 20",
    "temp_min": "27",
    "temp_max": "30",
    "scheds": [
        { "heure": "04", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "start"
            },
        { "heure": "08", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "stop"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "stop"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV3",
            "action": "start"
            },
        { "heure": "22", 
            "minutes": "00",
            "objet": "pompeV3",
            "action": "stop"
            },
        { "heure": "12", 
            "minutes": "00",
            "objet": "polaris",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "00",
            "objet": "polaris",
            "action": "stop"
            },
    ],
   },
   {
    "type": "type7",
    "desc": "temp sup a 30°C", 
    "duree_filtration_totale": "24",
    "temp_min": "30",
    "temp_max": "100",
    "scheds": [
        { "heure": "00", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "start"
            },
        { "heure": "08", 
            "minutes": "00",
            "objet": "pompeV1",
            "action": "stop"
            },
        { "heure": "80", 
            "minutes": "00",
            "objet": "pompeV2",
            "action": "start"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV2",
            "action": "stop"
            },
        { "heure": "11", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV4",
            "action": "stop"
            },
        { "heure": "14", 
            "minutes": "30",
            "objet": "pompeV3",
            "action": "start"
            },
        { "heure": "23", 
            "minutes": "50",
            "objet": "pompeV3",
            "action": "stop"
            },
        { "heure": "12", 
            "minutes": "00",
            "objet": "polaris",
            "action": "start"
            },
        { "heure": "14", 
            "minutes": "00",
            "objet": "polaris",
            "action": "stop"
            },
    ],
   },

]



## -+- FONCTIONS -+-
def arret_msg( msg ):
    """
       arret_msg( msg ): Arrete le programme avec ce message
    """
    print(msg)
    exit(1)

def file_exists(path):
    """
       file_exists(path): Test whether a path exists.  Returns False for broken symbolic links
    """
    try:
        st = os.stat(path)
    except os.error:
        return False
    return True

def timestamp():
    """
       timestamp(): Generate a string as timestamp : YYYYMMDD_HHMMSS.sss
    """
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%Y%m%d_%H%M%S.', localtime) + milliseconds

def server_help():
    """
       help() : renvoie dans stdout et dans une chaine l'aide en ligne
     :params:
     :returns: string contenant la doc en ligne
    """
    print(__doc__)
    return __doc__

def _mylog(caller, severity, msg):
    """
       mylog(caller, severity, msg): prints a message with a timestamp
    :param caller: function which called this routine
    :param severity: severity (INFO, DEBUG, WARN, ERROR, CRIT)
    :param msg: message to display (will be enriched)
    :return: none
    """
    global g_compteur_messages
    TS = timestamp()
    fmsg = "[{}:{}-{}-{}] {}".format(TS, g_compteur_messages, caller, severity, msg)
    print(fmsg)




def _msg_dbg(message):
    """
        _msg_dbg(message): affiche le msg si on est en mode debug
        severity : prefixe
    """
    if mode_debug:
        _mylog(" ", "DEBUG", message)


def get_function_name():
    return traceback.extract_stack(None, 2)[0][2]



def sep():
    _mylog(" ", "-", "=*"*40)

def get_env():
    """
       get_env(): Recupere qqs variables d'environnement, les stocke en interne
    """

def gen_schedule_from_file(fic):
    """
        gen_schedule_from_file(fic): Genere une liste de schedules depuis un fichier JSON 
        arg1 : fichier a charger
        returns schedule
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "Charge des schedules depuis fichier '{}'".format(fic))
    with open(fic, "r") as fp:
        sched = json.load(fp)
    return(sched)



def gen_schedule_file_json( sched, fic):
    """
        gen_schedule_file_json( sched, fic): Genere un fichier JSON contenant un ou tous les schedules 
        arg1 : fichier a generer
        arg2 : schedule
        returns OK ou ERR
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "Genere un fichier JSON '{}' contenant un ou tous les schedules ".format(fic))
    sched_json = json.dumps(sched)
    ## print(type(sched))
    with open(fic, 'w') as fp:
        json.dump(sched, fp)
    print("Fichier '{}' genere.".format(fic))
    return(code_ok)


def gen_schedule_par_temp(temp):
    """
        gen_schedule_par_temp(temp): renvoie un schedule fonction d'une temperature
        arg : temperature
        returns dict = schedule
        en pratique le schedule renvoye est un sous-item de schedule
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "renvoie un schedule fonction d'une temperature {}".format(temp))
    sched = list()

    nb_items = len(schedule)
    print("cherche temp '{}' parmi les {} schedules".format(temp, nb_items))
    it = 0
    while it < nb_items:
        sep()
        print(type(schedule[it]))
        pprint.pprint(schedule[it])

        if temp >= float(schedule[it]["temp_min"]) and temp < float(schedule[it]["temp_max"]):
            print("OK plage {}".format(it))
            sched = schedule[it]
            break
        else:
            print("NON pas dans la plage {}".format(it))
        it += 1
    print("OK on a trouve it={} desc '{}'".format(it, sched["desc"]))
    return(sched)


def gen_crontab( sched, temp ):
    """
       gen_crontab( sched, temp ): On cree une chaine crontab depuis l'objet Schedule trouvé
       args : schedule, temp 
       returns : string au format crontab
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "On cree une chaine crontab depuis l'objet Schedule trouvé")
    createur = "moimoi"
    date_creation = "2023/04/10"
    heure_creation = "18h45"
    ## script = rep_scripts/rac_script-objet-action.sh
    ##      ..../xxx-pompeV2-start.sh
    
    ## sched["scheds"]
    rep_scripts = "/home/scripts"
    rac_script = "sched"
    ext_script = "sh"
    
    crontab_str = """## Schedule genere le {} a {} par {}
## Temp mesuree : {}
## Schedule pour temps entre {} et {}
## desc du schedule de type {} : {}
## nb d'heures de filtration : {}
##

""".format(date_creation, heure_creation, createur, temp,
            sched["temp_min"], sched["temp_max"], 
            sched["type"], sched["desc"], 
            sched["duree_filtration_totale"])

    it=0
    nb_items = len(sched["scheds"])
    while it < nb_items:
        sep()
        print("{} {} -> {} sur {}".format(sched["scheds"][it]["heure"], sched["scheds"][it]["minutes"], 
                                          sched["scheds"][it]["action"], sched["scheds"][it]["objet"]))
        script = "{}/{}-{}-{}.{}".format(rep_scripts, rac_script, sched["scheds"][it]["objet"], sched["scheds"][it]["action"], ext_script)
        crontab_str += """{} {} * * * {}
""".format(sched["scheds"][it]["minutes"], sched["scheds"][it]["heure"], script)
        it += 1

    return(crontab_str)




def display_schedule(sched):
    """
        display_schedule(sched): Affiche le contenu d'un schedule (ou une liste)
        arg : schedule ou liste de schedules
     TODO: faire un chronogrtamme
    """
    pprint.pprint(sched)


def get_temp_domoticz (device_rid):

    """
       get_temp_domoticz (device_rid): Recupere la temperature de l'eau de la piscine via Domoticz
      arg : device id
      out : temperature (float) sans unite (°C ici)
        si -1 -> erreur
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "Recupere la temperature de l'eau de la piscine via Domoticz")    
    domoticzurl = 'http://dgbaley:8080'
    uclair = monenv.get_user()
    pclair = monenv.get_pwd()

    domoticz_req = ('{}/json.htm?type=devices&rid={}'.format(domoticzurl, device_rid))
    http = urllib3.PoolManager()
    myHeaders = urllib3.util.make_headers(basic_auth='%s:%s' % (uclair, pclair))

    resp = http.request('GET', domoticz_req, headers=myHeaders)
    _msg_dbg(resp)
    if resp.status != 200:
        print("Erreur : mauvaise requete '{}', code '{}'".format(domoticz_req, resp.status))
        _msg_dbg("Erreur : mauvaise requete '{}', code '{}'".format(domoticz_req, resp.status))
        ## return (json.dumps({}))
        return (-1)
    

    res_body = resp.data
    _msg_dbg(res_body)
    datajson = json.loads(res_body.decode('utf-8'))
    _msg_dbg(type(datajson))
    # msg(pprint.pprint(datajson))
    _msg_dbg(type(datajson['result'][0]))
    temp1 = (datajson['result'][0]['Data'])
    ## recoit '17.4 C'

    temptab = temp1.split()
    temp = float(temptab[0])
    _msg_dbg("Temp : {}".format(temp))
    
    return (temp)



## -=-=-=-=-=- MAIN -=-=-=-=-=-

monenv = MonEnv()
my_function_name = "main"
_mylog(my_function_name, "INFO", "Démarrage ....")    

if mode_debug:
    print("user : '{}'".format(monenv.get_user()))
    print("pwd : '{}'".format(monenv.get_pwd()))
    print("repscripts : '{}'".format(monenv.get_scripts_dir()))

## check qqs valeurs
## mode_debug = not mode_debug

if mode_debug:
    _msg_dbg(type(schedule))
    pprint.pprint(schedule)
    _msg_dbg(type(schedule[2]["scheds"][1]))
    _msg_dbg((schedule[2]["scheds"][1]))
## mode_debug = not mode_debug


## 
if mode_debug:

    gen_schedule_file_json(schedule, 'schedules1.json')
        
    schedule2 = gen_schedule_from_file("schedules.json")

    display_schedule(schedule)

    sep()

    display_schedule(schedule2)


temp = get_temp_domoticz(domoticz_device_rid)

## temp = 9.9
## temp = 10


print("Temperature : '{}'".format(temp))

sched_courant = gen_schedule_par_temp(temp)
display_schedule(sched_courant)

macrontab = gen_crontab(sched_courant, temp)

sep()
print(macrontab)
sep()




