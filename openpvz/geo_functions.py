from geoalchemy2 import Geography
from geoalchemy2.functions import GenericFunction

class ST_Distance(GenericFunction):
    name = 'ST_Distance'
    type = Geography
