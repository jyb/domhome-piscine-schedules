#!/bin/bash

## recupere les datas des devices lies a la piscine

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

let d=0
while [ $d  -lt ${#TAB_DEVICE_NAME[*]} ] ; do
     ## TEMP_PISCINE=$(curl -u "${SCHED_DOMOTICZ_USER}:${SCHED_DOMOTICZ_PASSWD}" -s  "http://${SCHED_DOMOTICZ_SERVER_NAME}:${SCHED_DOMOTICZ_SERVER_PORT}/json.htm?type=devices&rid=108" | jq '.result[0].Data' | sed -e 's/"//g' | awk '{print $1}') ; echo "$TEMP_PISCINE"
     ##  -> 13.5
     DATA[d]=$(curl -u "${SCHED_DOMOTICZ_USER}:${SCHED_DOMOTICZ_PASSWD}" -s  "http://${SCHED_DOMOTICZ_SERVER_NAME}:${SCHED_DOMOTICZ_SERVER_PORT}/json.htm?type=devices&rid=${TAB_DEVICE_IDX[d]}" | jq '.result[0].Data' | sed -e 's/"//g' | awk '{print $1}')
     echo "${TAB_DEVICE_NAME[d]} (${TAB_DEVICE_IDX[d]}) -> ${DATA[d]}"
     let d=d+1
done

echo "Datas collectees : ${DATA[*]}"
