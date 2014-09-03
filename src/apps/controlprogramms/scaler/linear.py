#!/usr/bin/python
# -*- coding: ascii -*-


class LinearScaler:
    """ Scale a value to an other, according to the linear equation.

    Attributes:
        _m (float): gradient
        _n (float): Value of y at x = 0
    """
    
    def __init__(self, y1, x1, y2, x2):
        """ Calculate "_m" and "_n" from two points of the linear equation.
        Args:
            y1 (float): y-Value of the first point.
            x1 (float): x-Value of the first point.
            y2 (float): y-Value of the second point.
            x2 (float): x-Value of the second point.
        """
        self._m = ((float)(y2)-(float)(y1)) / ((float)(x2)-(float)(x1))
        self._n = (float)(y1)-(float)(x1) * self._m
    
    def get_y(self, x):
        """ Returns the y-Value by given x-Value. """
        return self._m*x + self._n
    
    def get_x(self, y):
        """ Returns the x-Value by given y-Value. """
        return (y-self._n) / self._m
    
    def get_m(self):
        """ Returns "_m". """
        return self._m
    
    def get_n(self):
        """ Returns "_n". """
        return self._n

