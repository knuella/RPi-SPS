Tutorial zur RPi-SPS
====================

Hintergrundprogramme starten
""""""""""""""""""""""""""""

MongoDB starten
~~~~~~~~~~~~~~~

.. code:: bash

  sudo systemctl start mongodb

oder

.. code:: bash

  sudo service mongodb start

Ins repository Verzeichniss wechseln:

.. code:: bash

  cd rpi-sps/src

RPi-SPS starten
~~~~~~~~~~~~~~~
Controller starten (Name nach Klassendiagramm = NachrichtenVerwalter):

.. code:: bash

  python3 message_broker.py

configuration_manager starten unter dem namen "cm" mit den ip-adressen und
ports, die in der controler conf-datei gespeichert sind. (Name nach
Klassendiagramm = KonfigurationsVerwalter):

.. code:: bash

  python3 configuration_manager_mongodb.py cm tcp://127.0.0.10:6666 tcp://127.0.0.10:6665 tcp://127.0.0.10:5556 tcp://127.0.0.10:5555


template_manager starten unter dem namen "tm" mit den ip-adressen und
ports, die in der controler conf-datei gespeichert sind. (Name nach
Klassendiagramm = KonfigurationsVerwalter):

.. code:: bash

  python3 template_manager.py cm tcp://127.0.0.10:6666 tcp://127.0.0.10:6665 tcp://127.0.0.10:5556 tcp://127.0.0.10:5555

RPi-SPS mittels Startskript starten
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Die obrigen Befehle werden auch durch das "Startscript.sh" ausgeführt.

.. code:: bash
  
  ./Startscript.sh

Nachrichten verschicken / empfangen aus python
""""""""""""""""""""""""""""""""""""""""""""""
Python Konsole starten:

.. code:: bash

  python3

Den Socket zur Kommunikation einrichten:

.. code:: python

  import sys
  from rpisps.context import 

  #argumente für Context
  sys.argv = ['bla', 'test_context', 'tcp://127.0.0.10:6666', 'tcp://127.0.0.10:6665', 'tcp://127.0.0.10:5556', 'tcp://127.0.0.10:5555']

  #Context instanzieren
  test_context = Context()

Kommunikation mit dem ConfigManager:

.. code:: python

  #alle templates abfragen
  test_context.request_value('cm', {'operation':'read', 'collection':'templates', 'target':{})

  # config speichern
  test_context.write_value('cm', {'operation':'create', 'collection':'instances', 'target':{'blakey':'blubval'})

  # config abfragen
  test_context.request_value('cm', {'operation':'read', 'collection':'instances', 'target':{})

  # config löschen
  test_context.write_value('cm', {'operation':'update', 'collection':'instances', 'target':{'object_id':'1234345tesfvcjkdcfnhexr6387', 'blakey':'blubblubval'})
  
  # config löschen
  test_context.write_value('cm', {'operation':'delete', 'collection':'instances', 'target':'1234345tesfvcjkdcfnhexr6387'})

Kommunikation mit dem TemplateVerwalter (die Templates könne vorher als Liste mit der operation "read" abgefragt werden):

.. code:: python

  #neue Templates aus dem Templateordner (apps/templates) in die Datenbank schreiben:
  test_context.request_value('tm', {'operation':'equalize', 'target':'not_listed'})
  
  #geänderte Templates aus dem Templateordner (apps/templates) lesen und in der DB aktualsieren:
  test_context.request_value('tm', {'operation':'equalize', 'target':'modified'})
  
  #gelöschte Templates, die nicht mehr im Templateordner sind, auch in der DB löschen:
  test_context.request_value('tm', {'operation':'equalize', 'target':'deleted'})


