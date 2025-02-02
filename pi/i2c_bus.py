import smbus2

"""
Needed so that every subsequent file has 
the SAME reference to the bus:
ie. we don't want overlapping reference to bus 1
by magnet.py and accelerometer.py
"""

bus = smbus2.SMBus(1)