# Imports
import aft_log
import collections

def format_phone_details(os_version, device_manufacturer):
    print "Formatting phone details..."
    # Start formatting
    os_version = 'Android OS ' + os_version
    if (device_manufacturer == 'unknown'):
        device_manufacturer = 'Google'
    if (device_manufacturer == 'Unknown'):
        device_manufacturer = 'Google'
        
    aft_log.log("formatDBs: -> Data formatted successfully.", 0)
    details = collections.namedtuple('Details', ['x', 'y'])
    p = details(os_version, device_manufacturer)
    return p