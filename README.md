# domhome-piscine-schedules
Gestion des schedules des periphs piscine
![Repos !](images/Image_piscine.png)


# Histo
![Avant on avait ceci :](images/Ancien_scheduler-2022.png)

## Du cote de la pompe Chlore : SEKO PE 1.5
Debit : 1,5l/heure = 25ml/mn

 - la faire tourner qd la pompe piscine fonctionne
 - ne pas la faire tourner qd le polaris fonctionne
 - la faire tourner plutot le matin
Selon temperature et le type de traitement (Low, Medium ou High) on affiche la dose (ml) et le temps (minutes) :

| Température |    Low   |  Medium  |   High   |
|-------------|----------|----------|----------|
|  T < 15°C   |    ---   |   ---    |    ---   |
| 15 < T < 20 | 276 - 11 | 413 - 17 | 620 - 25 |
| 20 < T < 25 | 332 - 13 | 498 - 20 | 747 - 30 |
| 25 < T < 30 | 400 - 16 | 600 - 24 | 900 - 36 |
|  T > 30 °C  | 468 - 19 | 702 - 28 |1053 - 42 |



## Notes de bas de page
Voir https://forge.foundation4flight.solutions/gitlab/Akbar/PhebusGetData/-/blob/master/README.md
