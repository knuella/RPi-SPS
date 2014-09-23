from rpisps.exceptions import *


class ExclusiveWritebal(object):
    """ Extends normal variables, to bring the functionality
    of writing controle. If you want to write the value, you have to give the
    string stored in exclusive.
    Attributes:
        _exclusive (string): False, if everyone can write the variable, else
                             the given string have to match for writing.
        _value (dynamic): the value of the variable
    """
    def __init__(self, value, exclusive=None):

        self._value = value
        self._exclusive = exclusive
    
    def get_value(self):
        return self._value
   

    def set_value(self, new_value, exclusive):
        
        if not self._exclusive or self._exclusive == exclusive:
            self._value = new_value
        else:
            message = "The programm "+ self._exclusive + \
                      " have exclusive writing rights on this value."
            raise ExclusiveBlockError(message)
    
    def get_exclusive(self):
        if self._exclusive:
            return self._exclusive
        else:
            return "None"
    

    def set_exclusive(self, new_exclusive):
        
        if self._exclusive != new_exclusive:
            if self._exclusive == None:
                self._exclusive = new_exclusive
            else:
                message = "The exclusive flag is already set by " + \
                           self._exclusive + \
                           " and should be only canged by this programm."
                raise ExclusiveBlockError(message)
    

    def del_exclusive(self, exclusive):
        
        if self._exclusive == exclusive:
            self._exclusive = None
        else:
            message = "The exclusive flag is set by " + self._exclusive + \
                      " and should be only reset by this programm."
            raise ExclusiveBlockError(message)


