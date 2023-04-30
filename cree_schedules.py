#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :


"""
    cree_schedules.py : creation des schedules piscine (creation de crontabs en attendant mieux)

    JYB - 2023/04/10

    
Fonction de la temperature piscine (idealement une moyenne de la veille a la meme heure ou a la meme date l'annee d'avant, TBC),
on cree un schedule pour :
   - la pompe principale de la piscine : 4 vitesses (V1 V2 V3 V4) et horloge pour chacune
   - la pompe de Chlore liquide
   - le polaris

Selon la temperature piscine, on a 6 schedules differents pour la pompe principale et le Polaris:


|--------------|-------|------|------|------|------|---------|------------|--------|-------|------------|---------|--------|
| Temp piscine |     horaires start (B) et stop (E) de chaque vitesse (VX) et Polaris, d'apres schema Cathie 2023          |
|              |-------|------|------|------|------|---------|------------|--------|-------|------------|---------|--------|
|              | 00:00 | 03:00| 04:00| 06:00| 07:00|  08:00  |   11:30    |  12:00 | 14:00 |     14:30  |  20:00  |  22:00 |
|--------------|-------|------|------|------|------|---------|------------|--------|-------|------------|---------|--------|
|Temp < 10°C   |       |      | B.V1 | E.V1 |      |         |            |        |       |            |         |        |    
|10 < Temp < 12|       |  B.V1|  V1  |   V1 | E.V1 |         |            |        |       |            |         |        |    
|12 < Temp < 16|  B.V1 |  V1  | E.V1 |      |      |         |    B.V4    |  B.Pol | E.Pol |     E.V4   |         |        |
|16 < Temp < 24|       |      |      |      |      |  B.V2   |  E.V2-B.V4 |  B.Pol | E.Pol |  E.V4-B.V3 |   E.V3  |        |
|24 < Temp < 27|       |      |      |      |      |  B.V2   |  E.V2-B.V4 |  B.Pol | E.Pol |  E.V4-B.V3 |         |   E.V3 |
|27 < Temp < 30|       |      | B.V1 |      |      |E.V1-B.V2|  E.V2-B.V4 |  B.Pol | E.Pol |  E.V4-B.V3 |         |   E.V3 |
|--------------|-------|------|------|------|------|---------|------------|--------|-------|------------|---------|--------|

NOTA: 
 - verifier que la pompe principale marche quand on active le Polaris, ou la pompe de chlore liquide 
   (et verifier que le Polaris ne fonctionne pas qd on delivre le chlore)


Du cote de la pompe Chlore : SEKO PE 1.5

Pompe péristaltique Seko PE 1.5 l/h (kit WTD) 
(https://www.quimipool.com/fr/817-pompe-peristaltique-seko-pe-15-l-h-kit-wtd.html)

SEKO : Catalogue général : traitement d'eau (PDF) 
(https://cdn.seko.com/s/50959390-4f61-4be9-9fff-92c4da6ad670%2FCatalogue+Ge%CC%81ne%CC%81ral+Traitement+d%27Eau.pdf)


Debit : 1,5l/heure = 25ml/mn

 - la faire tourner qd la pompe piscine fonctionne
 - ne pas la faire tourner qd le polaris fonctionne
 - la faire tourner plutot le matin
Selon temperature et le type de traitement (Low, Medium ou High) on affiche la dose (ml) et le temps (minutes) :


|-------------|----------|----------|----------|
| Température |    Low   |  Medium  |   High   |
|-------------|----------|----------|----------|
|  T < 15°C   |    ---   |   ---    |    ---   |
| 15 < T < 20 | 276 - 11 | 413 - 17 | 620 - 25 |
| 20 < T < 25 | 332 - 13 | 498 - 20 | 747 - 30 |
| 25 < T < 30 | 400 - 16 | 600 - 24 | 900 - 36 |
|  T > 30 °C  | 468 - 19 | 702 - 28 |1053 - 42 |
|-------------|----------|----------|----------|

Arbitrairement, on choisit le mode "Medium"
On a deja determine un schedule principal (pompe principale et Polaris) selon la temperature, 
on va ajouter un schedule pour la pompe Chlore qui prend en compte qd la pompe principale et le Polaris sont actives
-> schedule


A propos de la variable schedule (schedule pompe principale et Polaris) :
    Au depart on a une liste de schedules ; chacun est un tableau de dict ;
    chaque dict est un front montant ou descendant applique a un objet a une heure/minutes donnes
    donne ici en hard code, il y a 2 fonctions de chargement ou creation d'un JSON, donc on peut partir d'un JSON externe si besoin
    Normalement ce JSON doit etre deduit d'une requete a la gestion de la pompe piscine et a Domoticz.

  Le pb est qu'il n'y a pas (encore ?) d'interface a la pompe piscine, donc on est obligés de "tricher" :
   - on fait le paramétrage/horloge de la pompe piscine
   - on reporte ce paramétrage sur Domoticz -> interrupteurs/dispositifs virtuels)  
   - on s'appuie sur cette info QUI DOIT RESTER COHERENTE !
   - on applique les lois de 2 tableaux : 
       - tableau des schedules pompes (renseigné à la main ou partiellement via Domoticz)
       - tableau de ce qu'il faut envoyer comme quantité de chlore par jour fonction de la temperature

 

Lancement : 
$ export SCHED_DOMOTICZ_USER=bougon
$ export SCHED_SCRIPTS_DIR=/home/tmp
$ export SCHED_DOMOTICZ_PASSWD=passwd
$ python3 cree_schedules.py
Pas besoin de venv python, pas de modules particuliers



Ex de recup Temp piscine via Domoticz :
TEMP_PISCINE=$(curl -u "bougon:passwd" -s  "http://dgbaley:8080/json.htm?type=devices&rid=108" | jq '.result[0].Data' | sed -e 's/"//g' | awk '{print $1}') ; echo "$TEMP_PISCINE" 


https://pypi.org/project/urllib3/
https://urllib3.readthedocs.io/en/stable/reference/index.html


https://github.com/jyb/domhome-piscine-schedules.git
   jean-yves.buzenet@o2source.org
   

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
import getpass
import socket


## idx ou rid du dispositif (device) de la sonde de temperature dans Domoticz
domoticz_temp_device_rid='108'


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
   schedule : voir explications plus haut et dans README.md du projet
   pompre principale et Polaris
   version hard-codee, peut-etre surchargee par un fichier JSON
   voir les fonctions gen_schedule_file_json() et gen_schedule_from_file() 
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

"""
   Tableau de ce qu'il faut delivrer en Chlore selon la temperature

"""
infos_dosage_chlore = [
    {
    "type": "hiver",
    "desc": "temp inf a 15°C", 
    "duree_dose_total": "0",
    "temp_min": "-100",
    "temp_max": "15",
    },
    {
    "type": "type2",
    "desc": "temp entre 15°C et 20°C", 
    "duree_dose_total": "17",
    "temp_min": "15",
    "temp_max": "20",
    },
    {
    "type": "type3",
    "desc": "temp entre 20°C et 25°C", 
    "duree_dose_total": "20",
    "temp_min": "20",
    "temp_max": "25",
    },
    {
    "type": "type4",
    "desc": "temp entre 25°C et 30°C", 
    "duree_dose_total": "24",
    "temp_min": "25",
    "temp_max": "30",
    },
    {
    "type": "type5",
    "desc": "temp sup a 30°C", 
    "duree_dose_total": "28",
    "temp_min": "30",
    "temp_max": "100",
    },

]


## -+- FONCTIONS UTILES -+-
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

def aujourdhui():
    """
       aujourdhui(): Generate a string as timestamp : YYYY/MM/DD
    """
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%Y/%m/%d', localtime)

def monheure():
    """
       monheure(): Generate a string as timestamp : HH:MM
    """
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%H:%M', localtime)

def timestamp():
    """
       timestamp(): Generate a string as timestamp : YYYYMMDD_HHMMSS.sss
    """
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%Y%m%d_%H%M%S.', localtime) + milliseconds

def quisuisje():
    return(getpass.getuser())

def mamachine():
    return(socket.gethostname())

def monrepertoire():
    return  os.getcwd()


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
    fmsg = "[{}:{:5d}-{}-{}] {}".format(TS, g_compteur_messages, caller, severity, msg)
    print(fmsg)
    g_compteur_messages += 1



def sep():
    _mylog(" ", "-", "=*"*40)


def sep_dbg():
    if mode_debug:
        _mylog(" ", "-", "=*"*40)


def _msg_dbg(message):
    """
        _msg_dbg(message): affiche le msg si on est en mode debug
        severity : prefixe
    """
    if mode_debug:
        _mylog(" ", "DEBUG", message)


def get_function_name():
    return traceback.extract_stack(None, 2)[0][2]



def get_env():
    """
       get_env(): Recupere qqs variables d'environnement, les stocke en interne
    """


## -+- FONCTIONS PROJET -+-
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
        return: dict = schedule
        en pratique le schedule renvoye est un sous-item de schedule
        TODO: et si on ne trouve pas ? en fait cela veut dire que la structure d'entree est pourrie
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "renvoie un schedule fonction d'une temperature {}".format(temp))
    sched = list()

    nb_items = len(schedule)
    _mylog(my_function_name, "INFO", "cherche temp '{}' parmi les {} schedules".format(temp, nb_items))
    it = 0
    while it < nb_items:
        sep_dbg()
        _msg_dbg(type(schedule[it]))
        _msg_dbg(display_schedule(schedule[it]))

        if temp >= float(schedule[it]["temp_min"]) and temp < float(schedule[it]["temp_max"]):
            _mylog(my_function_name, "INFO", "OK plage {}".format(it))
            sched = schedule[it]
            break
        else:
            _msg_dbg("NON pas dans la plage {}".format(it))
        it += 1
    _mylog(my_function_name, "INFO", "OK on a trouve it={} desc '{}'".format(it, sched["desc"]))
    return(sched)

def get_temps_dosage_selon_temp(temp):
    """
       get_temps_dosage_selon_temp(temp): renvoie le temps en minutes de dosage a appliquer selon la temperature
       info deduite de la liste de dict infos_dosage_chlore
       return: temps en minutes : duree_dosage
       TODO: et si on ne trouve pas ? en fait cela veut dire que la structure d'entree est pourrie
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "renvoie le temps en minutes de dosage a appliquer selon la temperature {}".format(temp))
    nb_items = len(infos_dosage_chlore)
    _mylog(my_function_name, "INFO", "cherche temp '{}' parmi les {} valeurs dosages".format(temp, nb_items))
    it = 0
    while it < nb_items:
        sep_dbg()
        _msg_dbg(type(infos_dosage_chlore[it]))
        _msg_dbg(display_schedule(infos_dosage_chlore[it]))

        if temp >= float(infos_dosage_chlore[it]["temp_min"]) and temp < float(infos_dosage_chlore[it]["temp_max"]):
            _mylog(my_function_name, "INFO", "OK plage {}".format(it))
            duree_dosage = infos_dosage_chlore[it]["duree_dose_total"]
            break
        else:
            _msg_dbg("NON pas dans la plage {}".format(it))
        it += 1
    _mylog(my_function_name, "INFO", "OK on a trouve it={} duree de dosage en minutes : {}".format(it, duree_dosage))
    return(int(duree_dosage))

def get_start_pompe_dans_sched_list(schedule1):
    """
       get_start_pompe_dans_sched_list(sched_list): renvoie la premiere heure:minutes a laquelle la pompe principale est demarree
       return: (heure, minutes, objet)   -> objet parmi V1, V2, ... 
       schedule1 est en pratique le schedule courant trouve par les autres recherches
       TODO: on prend le 1er item qui fait start, normalement c'est une pompe et pas le Polaris, mais bon c'est pas rigourteux ...

       Exemple :
        [{'action': 'start', 'heure': '08', 'minutes': '00', 'objet': 'pompeV2'},
        {'action': 'stop', 'heure': '11', 'minutes': '30', 'objet': 'pompeV2'},
        {'action': 'start', 'heure': '11', 'minutes': '30', 'objet': 'pompeV4'},
        {'action': 'stop', 'heure': '14', 'minutes': '30', 'objet': 'pompeV4'},
        {'action': 'start', 'heure': '14', 'minutes': '30', 'objet': 'pompeV3'},
        {'action': 'stop', 'heure': '20', 'minutes': '00', 'objet': 'pompeV3'},
        {'action': 'start', 'heure': '12', 'minutes': '00', 'objet': 'polaris'},
        {'action': 'stop', 'heure': '14', 'minutes': '00', 'objet': 'polaris'}]
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "renvoie la premiere heure:minutes a laquelle la pompe principale est demarree")

    s2_list = schedule1["scheds"] ## -> liste de schedules, le reste des champs de schedule1 n'est pas interressant
    nb_items = len(s2_list)
    it=0
    monitem = -1
    monheure = -1
    mesminutes = -1
    monobjet = "ZZ"
    trouve = False

    print("trouve {} items dans s2_list".format(nb_items))
    while it < nb_items:
        print("Cherche it = {} objet = '{}' ".format(it, s2_list[it]["objet"]))
        if trouve:
            print("Deja trouve, stop.")
        else:
    
            for k in s2_list[it].keys():
                if k == "action":
                    if s2_list[it]["action"] == "start":
                        print("trouve start it={} heure={}:{} obj='{}'".format(it, s2_list[it]["heure"], s2_list[it]["minutes"], s2_list[it]["objet"]))
                        monitem = it
                        monheure = s2_list[it]["heure"]
                        mesminutes = s2_list[it]["minutes"]
                        monobjet = s2_list[it]["objet"]
                        trouve = True
                        break

                    else:
                        print("trouve action '{}' it={}".format(s2_list[it]["action"], it))
                else:
                    print("==== it={} action pas trouvee on a k='{}'".format(it, k))
        it += 1

    return (int(monheure), int(mesminutes), monobjet, monitem)




def gen_schedule_chlore_par_temp_et_sched_gen(temp, h_depart, mn_depart, temps_dosage, sched_courant):
    """
        gen_schedule_chlore_par_temp_et_sched_gen(temp): renvoie un schedule fonction d'une temperature
              et du schedule principal deja calcule
        arg : temperature
              h_depart : heure effective
              mn_depart : minutes effectives
              temps_dosage
              schedule_principal
        returns dict = schedule_chlore
        il faut faire en sorte que la pompe chlore ne debite pas qd Polaris est ON ou pompe principale est OFF
        Astuce : le Polaris n'est pas le matin, le plus simple est de debiyter le matin dans les heures de la pompe
        TODO: temp : on s'en f... un peu dans cette routine
        Attention : on recoit les heures,minutes et temps_dosage comme des entiers, il faut reformatter pour genere des schedules a 2 caracteres

     """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "renvoie un schedule fonction d'une temperature {} et du schedule principal".format(temp))
    
    """
    Exemple :
    sched_chlore = [
        {'action': 'start', 'heure': '12', 'minutes': '10', 'objet': 'chlore'},
        {'action': 'stop', 'heure': '12', 'minutes': '00', 'objet': 'chlore'},
        ]
    """
    sched_chlore = list()
    mn_fin = mn_depart + temps_dosage
    h_fin = h_depart
    if mn_fin >= 60:
        mn_fin -=60
        h_fin = h_depart + 1

    d1 = dict()
    print(type(d1))
    d1["action"] = 'start'
    d1["heure"] = f'{h_depart:02d}'
    d1["minutes"] = f'{mn_depart:02d}'
    d1["objet"] = 'chlore'
    
    sched_chlore.append(d1)
    d1 = dict()
    d1['action'] = 'stop'
    d1['heure'] = f'{h_fin:02d}'
    d1['minutes'] = f'{mn_fin:02d}'
    d1['objet'] = 'chlore'
    
    sched_chlore.append(d1)

    return (sched_chlore)


def gen_crontab( sched, temp ):
    """
       gen_crontab( sched, temp ): On cree une chaine crontab depuis l'objet Schedule trouvé
       args : schedule, temp 
       returns : string au format crontab
    """
    my_function_name = get_function_name()
    _mylog(my_function_name, "INFO", "On cree une chaine crontab depuis l'objet Schedule trouvé")
    createur = "{}@{}".format(quisuisje(),mamachine()) ## "moimoi@mamachine"

    date_creation = aujourdhui() ## "2023/04/10"
    heure_creation = monheure() ## "18:45"
    ## script = rep_scripts/rac_script-objet-action.sh
    ##      ..../xxx-pompeV2-start.sh
    
    ## sched["scheds"]
    rep_scripts = monrepertoire()  ## "/home/scripts"
    rac_script = "sched"
    ext_script = "sh"
    
    crontab_str = """## Schedule genere le {} a {} par {}:{}
## Temp mesuree : {}
## Schedule pour temps entre {} et {}
## desc du schedule de type {} : {}
## nb d'heures de filtration : {}
##

""".format(date_creation, heure_creation, createur, rep_scripts,
           temp,
            sched["temp_min"], sched["temp_max"], 
            sched["type"], sched["desc"], 
            sched["duree_filtration_totale"])

    it=0
    nb_items = len(sched["scheds"])
    while it < nb_items:
        sep_dbg()
        _msg_dbg("{} {} -> {} sur {}".format(sched["scheds"][it]["heure"], sched["scheds"][it]["minutes"], 
                                          sched["scheds"][it]["action"], sched["scheds"][it]["objet"]))
        script = "{}/{}-{}-{}.{}".format(rep_scripts, rac_script, sched["scheds"][it]["objet"], sched["scheds"][it]["action"], ext_script)
        crontab_str += """{} {} * * * {}
""".format(sched["scheds"][it]["minutes"], sched["scheds"][it]["heure"], script)
        it += 1

    return(crontab_str)




def display_schedule(sched):
    """
        display_schedule(sched): Affiche le contenu d'un schedule (ou une liste)
        arg : schedule
        return: string -> pour _mylog() par exemple 
     TODO:liste de schedules
     TODO: faire un chronogramme
    """
    ret = pprint.pformat(object = sched, indent = 2, width = 100, depth = 3, sort_dicts = True )
    return ret


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





## -+- MAIN -+-

monenv = MonEnv()
my_function_name = "main"
_mylog(my_function_name, "INFO", "Démarrage ....")    

_mylog(my_function_name, "INFO", "Mode debug : {}".format(mode_debug))

## ==============================
## >>>>>  DEBUG BLOCK

# mode_debug = True
# mode_debug = not mode_debug
# _mylog(my_function_name, "INFO", "Mode debug : {}".format(mode_debug))


if mode_debug:
    _msg_dbg("user : '{}'".format(monenv.get_user()))
    _msg_dbg("pwd : '{}'".format(monenv.get_pwd()))
    _msg_dbg("repscripts : '{}'".format(monenv.get_scripts_dir()))

    ## check qqs valeurs
    ## mode_debug = not mode_debug

    display_schedule(schedule)
    # _msg_dbg(type(schedule))
    # pprint.pprint(schedule)
    # _msg_dbg(type(schedule[2]["scheds"][1]))
    # _msg_dbg((schedule[2]["scheds"][1]))

    ## Test de chargement et sauvegarde du schedule

    json_file_saved1 = "schedules1.json"
    json_file_orig = "schedules.json"
    _msg_dbg("Test : sauve schedule vers '{}'".format(json_file_saved1))
    gen_schedule_file_json(schedule, json_file_saved1)
        
    _msg_dbg("Test : charge schedule depuis '{}'".format(json_file_orig))
    schedule2 = gen_schedule_from_file(json_file_orig)

    _msg_dbg(
"""schedule du source :
---------------------------------------------------------------------------
{}
---------------------------------------------------------------------------
""".format(display_schedule(schedule)))

    _msg_dbg(
"""schedule charge depuis '{}' :
---------------------------------------------------------------------------
{}
---------------------------------------------------------------------------
""".format(json_file_orig, display_schedule(schedule2)))

    sep_dbg()
## <<<<<  DEBUG BLOCK
## ==============================


# -=- Recup temerature via Domoticz
temp = get_temp_domoticz(domoticz_temp_device_rid)

## DEBUG : forcer d'autres temps pour verifier les algos
## temp = 9.9
## temp = 10

_mylog(my_function_name, "INFO", "Temperature : '{}'".format(temp))

# -=- Creer schedule pompe principale et Polaris
sched_courant = gen_schedule_par_temp(temp)
_mylog(my_function_name, "INFO", "Schedule genere : '{}'".format(display_schedule(sched_courant)))

# -=- Generer le schedule de la pompe chlore
duree_dosage = get_temps_dosage_selon_temp(temp)
_mylog(my_function_name, "INFO", "duree de dosage en minutes : {}".format(duree_dosage))

## On recherche dans sched_courant le start de pompe le matin < start de polaris
## Attention : on recoit des int pour heures et minutes, il faudra ecrire dans ls scheduling '09' au lieu de '9' par exemple

(mh, mm, mo, mi) = get_start_pompe_dans_sched_list(sched_courant)

print("Trouve pour pompe : mh = {}, mm = {}, mo = {}, mi = {}".format(mh, mm, mo, mi))
h_depart = mh
mn_depart = int(mm) + 10
if mn_depart >= 60:
    mn_depart -=60
    h_depart +=1


sched_chlore = gen_schedule_chlore_par_temp_et_sched_gen(temp, h_depart, mn_depart, duree_dosage, sched_courant)
print("sched_chlore")
print(display_schedule(sched_chlore))
print("sched_courant")
print(display_schedule(sched_courant))

## Maintenant il suffit d'integrer sched_chlore dans les scheds de sched_courant
## TODO : pas joli, mais bon ....
sched_courant["scheds"].append(sched_chlore[0])
sched_courant["scheds"].append(sched_chlore[1])
print("NOUVEAU sched_courant")
print(display_schedule(sched_courant))


# -=- Generer la crontab complete
# TODO: integrer Pompe chlore
macrontab = gen_crontab(sched_courant, temp)

sep()
_mylog(my_function_name, "INFO", "Crontab generee : '{}'".format(macrontab))
sep()




