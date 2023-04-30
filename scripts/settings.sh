#!/bin/bash

## recupere les datas des devices lies a la piscine
## a sourcer dans les scripts faisant vraiment le taf

## Devices Domoticz
## Nom                  Idx    Materiel               ID Materiel   Donnees exemple
## Temp Piscine         108    Température Piscine    140BC          13.5 C
## Piscine OXAR         414    RelaisElijah           000141EE       Off
## Temp Garage          107    Température Garage     140BB          13.2 C
## Polaris              999    RelaisElijah           00014437       Off
## PompeIntellifowV1   1440    PompePiscine           000145F0       Off
## PompeIntellifowV2   1441    PompePiscine           000145F1       Off
## PompeIntellifowV3   1442    PompePiscine           000145F2       Off
## PompeIntellifowV4   1443    PompePiscine           000145F3       Off

TAB_DEVICE_NAME=(TempPiscine TempGarage PompeChlore Polaris PompeIntellifowV1 PompeIntellifowV2 PompeIntellifowV3 PompeIntellifowV4 )
TAB_DEVICE_IDX=(108 107 414 999 1440 1441 1442 1443 )


