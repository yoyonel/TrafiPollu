# Makefile

Makefile générer (initialement) par le plugin QGIS `Plugin Builder`

En seconde étape, il y a une customisation du Makefile pour correspondre au projet (effectif) lié au plugin qu'on développe (plugin TrafiPollu)

## Analyse (par parties) du fichier Makefile

Vu synthétique du Makefile modifié:
```makefile
...
# translation
SOURCES = \
	__init__.py \
  ...

PY_FILES = \
	interactive_map_tracking.py \
  ...

UI_FILES = interactive_map_tracking_dialog_base.ui

EXTRAS = \
    icon.png \
    metadata.txt \
    *.sql \
    *.xml \
    *.xsd \
    *.ini

COMPILED_RESOURCE_FILES = resources_rc.py
#################
# XSD           #
#################
# On selectionne par inclusion quelle version du XSD on souhaite utiliser pour générer le parser
COMPILED_RESOURCE_FILES += parser_symuvia_xsd_2_04_pyxb.py
#################

...

#################
# XSD           #
#################
# on extrait la version dans le nom du fichier
GET_XSD_VERSION = $(subst _,.,$(subst _pyxb.py,,$(subst parser_symuvia_xsd_,,$1)))

%_pyxb.py:
	@echo "----------------------------------"
	@echo "XSD : Generate Parser for SYMUVIA"
	@echo "----------------------------------"
    # $@ : fichier courant
    # $< : dependance
	pyxbgen -u reseau_$(call GET_XSD_VERSION,$@).xsd -m $(subst .py,,$@)
#################
```

### SOURCES/PY_FILES

Les deux variables se reflètent, elles contiennent la liste des sources pythons du projet.

### EXTRAS

- Scripts SQL:
  ```makefile
  *.sql
  ```
- Données par rapport au parser XML SYMUVIA
  ```makefile
  *.xml \
  *.xsd \
  ```
  + xml: utilisé pour instancier un arbre XML vide de projet SYMUVIA. Par la suite, on rajoute à cet arbre différentes 'branches' pour élargir, le remplir, etc ...
  + xsd: fichier .xsd décrivant le schéma des fichiers XML SYMUVIA (XSD: XML Schema Definition)

## COMPILED_RESOURCE_FILES

- `resources_rc.py`: build de `UI_FILES` utilisé pour le GUI (QT)
- `parser_symuvia_xsd_2_04_pyxb.py`: build de la génération du parser XML SYMUVIA (construit à partir de `*.xsd`)
  + XSD target: `parser_symuvia_xsd_2_04_pyxb.py`
    + nom/prefix: `parser_symuvia_xsd`
    + version: `2_04`
    + nom/suffix: `_pyxb`
  + Source XSD: `reseau_<version_XSD>.xsd`

### Targets principales du MakeFile

  - clean
  - compile
  - deploy
