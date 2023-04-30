#!/bin/bash

# Demarrage Polaris piscine 
#
#  interface numerique avec le Polaris, via des virtual switches sous Domoticz
# 

## Specifique a ce script
## MYDEVICE_NAME="PompeChlore"
## MYDEVICE_NAME="Polaris"
## MYDEVICE_NAME="PompeIntellifowV1"
## MYDEVICE_NAME="PompeIntellifowV2"
## MYDEVICE_NAME="PompeIntellifowV3"
## MYDEVICE_NAME="PompeIntellifowV4"
## MYCOMMAND="On"
## MYCOMMAND="Off"

MYDEVICE_NAME="Polaris"
MYCOMMAND="On"

## A partir d'ici, rien ne change ...
##
FILE_SETTINGS="./settings.sh"
if [ ! -f ${FILE_SETTINGS} ] ; then
    echo "Pas de fichier de settings '${FILE_SETTINGS}' accesible. Stop"
    exit 9
fi

source ${FILE_SETTINGS}

if [ -z ${SCHED_DOMOTICZ_USER+x} ] ; then
    echo "Var SCHED_DOMOTICZ_USER non initialisee. Stop."
    exit 1
fi

if [ -z ${SCHED_DOMOTICZ_PASSWD+x} ] ; then
    echo "Var SCHED_DOMOTICZ_PASSWD non initialisee. Stop."
    exit 2
fi

if [ -z ${SCHED_SCRIPTS_DIR+x} ] ; then
    echo "Var SCHED_SCRIPTS_DIR non initialisee. Stop."
    exit 3
fi

if [ -z ${SCHED_DOMOTICZ_SERVER_NAME+x} ] ; then
    echo "Var SCHED_DOMOTICZ_SERVER_NAME non initialisee. Stop."
    exit 4
fi

if [ -z ${SCHED_DOMOTICZ_SERVER_PORT+x} ] ; then
    echo "Var SCHED_DOMOTICZ_SERVER_PORT non initialisee. Stop."
    exit 5
fi

echo "OK SCHED_DOMOTICZ_USER = '${SCHED_DOMOTICZ_USER}'   SCHED_SCRIPTS_DIR = '${SCHED_SCRIPTS_DIR}'"

let i=0
let n1=${#TAB_DEVICE_NAME[*]}
let n2=${#TAB_DEVICE_IDX[*]}
if [ $n1 -ne $n2 ] ; then
    echo "PB pas le meme nb d'items entre TAB_DEVICE_NAME ($n1) et TAB_DEVICE_IDX ($n2)"
    exit 99
fi

while [ $i -ne $n1 ] ; do
    ## echo "$i : ${TAB_DEVICE_NAME[i]}"
    if [ "${TAB_DEVICE_NAME[i]}" = "${MYDEVICE_NAME}" ] ; then
        ## echo "Trouve $i"
	break
    else
	## echo "pas trouve $MYDEVICE_NAME : suivant"
	let i=i+1
    fi
done

DATA=$(curl -u "${SCHED_DOMOTICZ_USER}:${SCHED_DOMOTICZ_PASSWD}" -s  "http://${SCHED_DOMOTICZ_SERVER_NAME}:${SCHED_DOMOTICZ_SERVER_PORT}/json.htm?type=command&param=switchlight&idx=${TAB_DEVICE_IDX[i]}&switchcmd=${MYCOMMAND}")
echo "${TAB_DEVICE_NAME[i]} (${TAB_DEVICE_IDX[i]}) -> ${DATA}"

