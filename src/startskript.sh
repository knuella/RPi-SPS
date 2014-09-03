#!/usr/bin/bash

python3 message_broker.py&

python3 configuration_manager_mongodb_alt.py cm tcp://127.0.0.10:6666 tcp://127.0.0.10:6665 tcp://127.0.0.10:5556 tcp://127.0.0.10:5555&

python3 template_manager.py tm tcp://127.0.0.10:6666 tcp://127.0.0.10:6665 tcp://127.0.0.10:5556 tcp://127.0.0.10:5555&



