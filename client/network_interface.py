'''
network interface parameter
'''

import socket
from geolite2 import geolite2

def get_stun_server():
    '''
    return stun server ip
    '''

    return "192.168.1.98"

def get_signalling_server():
    '''
    return the ip and the port of signalling server
    '''

    return "192.168.1.98", 5000

def get_area(candidate):
    '''
    return the area where the reflex candidate in
    '''

    #reader = geolite2.reader()
    
    #reader.get(candidate.split(":")[0])
    #iso_code = reader['country']['iso_code']
    iso_code = "TW"

    #reader.close()

    return iso_code
