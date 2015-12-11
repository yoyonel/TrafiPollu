Les Composants du plugin TrafiPollu
===================================

Listes des principaux composants:
    - :ref:`trafipolluImp`.
    - :ref:`trafipolluImp_SQL`.
    - :ref:`trafipolluImp_DUMP`.
    - :ref:`trafipolluImp_TOPO`.
    - :ref:`trafipolluImp_EXPORT`.
        - :ref:`trafipolluImp_EXPORT_CONNEXIONS`.
        - :ref:`trafipolluImp_EXPORT_TRAFICS`.
    - :ref:`imt_tools`


.. _trafipolluImp:

trafipolluImp
-------------

Interface principale du Plugin

Détails de l'interface:

.. automodule:: trafipolluImp
    :members:
    :private-members:

.. _trafipolluImp_SQL:

trafipolluImp_SQL
-----------------

Module utilisé pour la gestion de communication SQL

Détails de l'interface:

.. automodule:: trafipolluImp_SQL
    :members:
    :private-members:

.. _trafipolluImp_DUMP:

trafipolluImp_DUMP
------------------

Module utilisé pour la gestion du DUMP d'informations BD-SreetGen -> Python

Détails de l'interface:

.. automodule:: trafipolluImp_DUMP
    :members:
    :private-members:


.. _trafipolluImp_TOPO:

trafipolluImp_TOPO
------------------

Module utilisé pour la gestion de la construction/conversion TOPOlogique BD-SreetGen -> SYMUVIA

Détails de l'interface:

.. automodule:: trafipolluImp_TOPO
    :members:
    :private-members:


.. _trafipolluImp_EXPORT:

trafipolluImp_EXPORT
--------------------

Module utilisé pour l'EXPORT SYMUVIA -> XML (via un parser PyXB issu d'un XSD SYMUVIA)

Détails de l'interface:

.. automodule:: trafipolluImp_EXPORT
    :members:
    :private-members:

.. _trafipolluImp_EXPORT_CONNEXIONS:

trafipolluImp_EXPORT_CONNEXIONS
-------------------------------

(sous) Module utilisé pour l'EXPORT-CONNEXIONS SYMUVIA -> XML (via un parser PyXB issu d'un XSD SYMUVIA)

Détails de l'interface:

.. automodule:: trafipolluImp_EXPORT_CONNEXIONS
    :members:
    :private-members:

.. _trafipolluImp_EXPORT_TRAFICS:

trafipolluImp_EXPORT_TRAFICS
----------------------------

(sous) Module utilisé pour l'EXPORT-TRAFICS SYMUVIA -> XML (via un parser PyXB issu d'un XSD SYMUVIA)

Détails de l'interface:

.. automodule:: trafipolluImp_EXPORT_TRAFICS
    :members:
    :private-members:


.. _imt_tools:

imt_tools
---------


Détails de l'interface:

.. automodule:: imt_tools
    :members:
    :private-members:
