Les Composants du plugin TrafiPollu
===================================

Listes des principaux composants:
    - :ref:`trafipolluImp`.
    - :ref:`trafipolluImp_SQL`.
    - :ref:`trafipolluImp_DUMP`.
    - :ref:`imt_tools`

BlockDiag:

.. blockdiag::

    blockdiag admin {
        A -> B
    }

graphviz:
.. graphviz::

   digraph {
      "From" -> "To";
   }

PlantUML:

.. uml::

    @startuml
    Alice -> Bob: Hi!
    Alice <- Bob: How are you?
    @enduml

.. uml::

   @startuml
   skinparam backgroundColor #EEEBDC

    skinparam sequence {
        ArrowColor DeepSkyBlue
        ActorBorderColor DeepSkyBlue
        LifeLineBorderColor blue
        LifeLineBackgroundColor #A9DCDF

        ParticipantBorderColor DeepSkyBlue
        ParticipantBackgroundColor DodgerBlue
        ParticipantFontName Impact
        ParticipantFontSize 17
        ParticipantFontColor #A9DCDF

        ActorBackgroundColor aqua
        ActorFontColor DeepSkyBlue
        ActorFontSize 17
        ActorFontName Aapex
    }

    actor Foo1
    boundary Foo2
    control Foo3
    entity Foo4
    database Foo5
    Foo1 -> Foo2 : To boundary
    Foo1 -> Foo3 : To control
    Foo1 -> Foo4 : To entity
    Foo1 -> Foo5 : To database

    actor User
    participant "First Class" as A
    participant "Second Class" as B
    participant "Last Class" as C

    User -> A: DoWork
    activate A

    A -> B: Create Request
    activate B

    B -> C: DoWork
    activate C
    C --> B: WorkDone
    destroy C

    B --> A: Request Created
    deactivate B

    A --> User: Done
    deactivate A

   @enduml

Salt:

.. uml::

    @startsalt
    {+
    {/ <b>General | Fullscreen | Behavior | Saving }
    {
        { Open image in: | ^Smart Mode^ }
        [X] Smooth images when zoomed
        [X] Confirm image deletion
        [ ] Show hidden images
    }
    [Close]
    }
    @endsalt


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


.. _imt_tools:

imt_tools
---------


Détails de l'interface:

.. automodule:: imt_tools
    :members:
    :private-members:
