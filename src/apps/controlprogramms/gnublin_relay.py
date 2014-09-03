#!/usr/bin/python
# -*- coding: ascii -*-
from opensps_exceptions import *
import gnublin


class GnublinRelayIO:
    """
    A class to connect to the hardware of a gnublin_module_relay as a plugin of
    the openSPS-project.
    
    It should be used to set the outputs (relays) on the modul, the actual value
    stored in the microcontroler can be read. 
    
    Attributes:
        _good (boolean): False, if during the last operation an error accourt. 
        _actual_value (int): last value, which was read.
        _modul (gnublin_module_relay): contains the funktionality to conntect to the
            hardware (from the gnublin api)
    """
    
    def __init__(self, modul_address, relay_address):
        """
        Initialize the object with the actual value reading from the hardware. 
        Initialize the actual value to 0, if there is an error during reading.
        
        Args:
            modul_address (int): hexadecimal z.B. 0x20
            relay_address (int): 1-4
        """
        self._good = False
        self._actual_value = 0
        
        self._modul = gnublin.gnublin_module_relay()
        self._modul.setAddress(modul_address)
        if relay_address >= 1 and relay_address <= 4:
            self._relay_address = relay_address
        else:
            raise InputError("relayAddress have to be between 1 and 4.")
        
        self.get_value()
    
    def set_value(self, to_set_value):
        """ Write a new value to the hardware.
        Sets the "_good"-flag.
        Args:
            to_set_value (real): Value that will be write.
        """
        if self._modul.switchPin(self._relay_address, to_set_value) != -1:
            self._good = True
        else:
            self._good = False

    def get_value(self):
        """ Read the value from the hardware.
        Sets the "_good"-flag.
        """
        value = self._modul.readState(self._relay_address)
        if value != -1:
            self._actual_value = value
            self._good = True
            return self._actual_value
        else:
            self._good = False
    
    def get_good(self):
        """ Returns false, if the last operation don't reach its goal.
        Otherwise returns true.
        """
        return self._good
        return self._good



