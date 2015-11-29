# Installation VM pour TrafiPollu

## Choix de la distribution
![Logo LUbuntu](lubuntu1.png)
+ LUbuntu **14.04** 64bits:
[http://cdimage.ubuntu.com/lubuntu/releases/14.04/release/](http://cdimage.ubuntu.com/lubuntu/releases/14.04/release/)

## Installation
### Login/Password
login/password: trafipollu/trafipollu

### Settings Proxy pour l'IGN

### Insert Guest Additions CD Images
```bash
$ cd /media/trafipollu/VBOXADDITIONS_4.3.34_104062/
$ sudo ./VBoxLinuxAdditions.run
```
=> reboot

### APT Update/Upgrade
```bash
$ sudo apt-get update
$ sudo apt-get upgrade
```
- apt-file: utile pour retrouver les packages associes à un fichier
```bash
$ sudo apt-get install apt-file
$ apt-file update
```

### Installation QGIS
Depuis les dépots:
```bash
$ sudo apt-get install qgis
```
~ 500 mo pour l'installation (selon apt)

Version installée: QGIS - 2.0.1-Dufour 'Dur' (exported)

Cette version n'est pas assez "récente" (<2.6) pour faire tourner le plugin

#### Installation QGIS version plus récente
ubuntu-fr QGIS: [lien](http://doc.ubuntu-fr.org/qgis)
- [Pour obtenir la version courante ou la LTS via un PPA](http://doc.ubuntu-fr.org/qgis#pour_obtenir_la_version_courante_ou_la_lts_via_un_ppa)

  -> pour la version courante de QGIS : ppa:ubuntugis/ubuntugis-unstable1
```bash
$ sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
$ sudo apt-get update
$ sudo apt-get upgrade
$ sudo apt-get install qgis
$ sudo apt-get install python-qgis
```

Normalement ça install la version 2.8

### Installation pgAdmin3
```bash
$ sudo apt-get install pgadmin3
```
~ 20 mo

### Configuration d'un réseau pour communication entre deux VMs

* Probleme: du mal à régler 'localhost' entre deux guest VMs (fonctionne correctement pour l'host.)
* Solution: utiliser un réseau interne (internal network) pour communiquer directement entres les VMs (comme si elles étaient connectées à un switch/routeur)
Tutorial suivi:
  * Pro: ça fonctionne :)
  * Con: il faut spécifier (à la main) l'adresse (ip) du serveur PostGres (ip de la VM faisant tourner le serveur PostGres)

[connecting 2 virtual machines using virtualbox](https://www.youtube.com/watch?v=nR_cE2xnwEs)
```bash
VBoxManage dhcpserver add --netname intnet \
                          --ip 10.0.1.1 --netmask 255.255.255.0 \
                          --lowerip 10.0.1.2 --upperip 10.0.1.200 --enable
```

On peut alors récupérer les adresses ip (internes) des VMs, en particulier celle de la VM accueillant le serveur PostGres:
```bash
$ ifconfig | grep "inet" | grep "10.0.1"
```
On devrait récupérer: 10.0.1.[1|2] (selon l'ordre de lancement des VMs)

On peut régler un fichier projet QGIS (.qgs) pour pointer vers ce serveur:
```bash
$ sed 's/localhost//g' <qgis_project_for_local_streetgen> > <qgis_project_for_inet_streetgen>
```
avec (dans mon cas):
```bash
<inet_address>: 10.0.1.2
<qgis_project_for_local_streetgen>: 2015_11_28_StreetGen_local_server.qgs
<qgis_project_for_inet_streetgen>: 2015_11_29_StreetGen_4_internal_server.qgs
```

### Recupération du plugin: Interactive Map Tracking pour TrafiPollu

#### On recupère les sources du plugin

##### GIT
Utilisation (dans mon cas) de GIT pour cloner le directory du projet (sur github).
```bash
$ sudo apt-get install git
```
~ 20mo

```bash
$ git clone https://github.com/yoyonel/TrafiPollu
$ git checkout TrafiPollu
```

#### Outils pour build/deploy le plugin QGIS

##### Make
```bash
$ sudo apt-get install make
```

##### Python Dev
```bash
$ sudo apt-get install python-dev
```
~ 35mo

##### Installation de PyQt4
Ubuntu Fr PyQt: http://doc.ubuntu-fr.org/pyqt
```bash
$ sudo apt-get -y install python-qt4
```
```bash
$ sudo apt-get -y install pyqt4-dev-tools
```

##### Pip : récupération des modules python
```bash
$ sudo apt-get install python-pip
```
~ 100mo

+ PyXB: génération parser XML depuis XSD
```bash
$ sudo -E pip install PyXB
```
  + pyxbgen

+ Sphynx:
```bash
$ sudo -E pip install Sphynx
```

##### Compilation (deploy) du plugin
On lance la compilation/build/deploy du plug:
```bash
$ ./build_and_deploy.sh
```

On redémarre QGIS et dans 'Extensions' on devrait voir apparaitre 'Interactive Map Tracking'

##### Lib/Modules Python utilisés par le plugin
```bash
$ sudo -E pip install <python-module>
```

Si problème d'installation/compilation (du module C d'optimisation),
satisfaire les dépendances manquantes (via apt-get) et reinstaller le module:
```bash
$ sudo -E pip install --upgrade --force-reinstall <python-module>
```

- networkx
- shapely:

  Dev. packages [-dev] for:
  - libxml2
  - libxslt
  - libgeos

- lxml

  Si probleme avec -lz:  
```bash
$ updatedb; locate libz.so
```

  Devrait apparaitre un .so.1, il faut créer un lien symbolique vers ce .so:
```bash
$ ln -s <path_to_libz.so.1>/libz.so.1 <path_to_libz.so.1>/libz.so
```

- psycopg2:
  Dev. packages for:
  - libpq-dev

  -> Verification:
```bash
$ echo "import psycopg2; print psycopg2.__version__" | python  
```

#### Setting: Config file INI for TrafiPollu
Pensez à changer 'host' dans le fichier .ini utiliser par le module SQL
```ini
[SQL_SERVER_LOCAL]
host: <ip_VM_host_PostGres_server>
```
dans mon cas:
```ini
ip_VM_host_PostGres_server = 10.0.1.2
```

## Test visualisation des résultats de l'export

### "Installation" de SymuNet

#### Wine
```bash
$ sudo apt-get install wine
```
~ 640mo

#### Scripts pour lancer SymuNet
