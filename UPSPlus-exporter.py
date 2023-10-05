#!/usr/bin/env python3

# Description：
'''This is the demo code for all the functions of UPS Plus.
https://wiki.52pi.com/index.php?title=EP-0136

Advanced users can select the functions they need through the function options provided in the code below to customize and develop them to meet their needs.
See https://github.com/geeekpi/upsplus/tree/main
'''

import argparse
import time
import smbus2
import logging
from ina219 import INA219,DeviceRangeError

"""
usage: UPSPlus-exporter.py [-h]

optional arguments:
  -h, --help            show this help message and exit
  -r, --raw             print raw data to stddout
  --influxdb            publish to influxdb
  --influxdb_host INFLUXDB_HOST
                        hostname or ip of InfluxDb HTTP API
  --influxdb_port INFLUXDB_PORT
                        port of InfluxDb HTTP API
  --influxdb_user INFLUXDB_USER
                        InfluxDb username
  --influxdb_pass INFLUXDB_PASS
                        InfluxDb password
  --influxdb_db INFLUXDB_DB
                        InfluxDb database name
  -v, --verbose         verbose output to watch the threads
"""



#----------------

def influxdb_publish(event, data):
    from influxdb import InfluxDBClient

    if not data:
        print("Not publishing empty data for: ", event)
        return

    try:
        client = InfluxDBClient(host=args.influxdb_host,
                                port=args.influxdb_port,
                                username=args.influxdb_user,
                                password=args.influxdb_pass,
                                database=args.influxdb_db)
        payload = {}
        payload['measurement'] = event

        payload['time']   = int(time.time())
        payload['fields'] = data

        if args.verbose:
            print ("publishing %s to influxdb [%s:%s]: %s" % (event,args.influxdb_host, args.influxdb_port, payload))

        # write_points() allows us to pass in a precision with the timestamp
        client.write_points([payload], time_precision='s')

    except Exception as e:
        print("Failed to connect to InfluxDB: %s" % e)
        print("  Payload was: %s" % payload)

#----------------

DEVICE_BUS = 1
DEVICE_ADDR = 0x17
PROTECT_VOLT = 3700
SAMPLE_TIME = 2

def publish_raspberry_pi_data():
        ina_supply = INA219(0.00725, busnum=DEVICE_BUS, address=0x40)
        ina_supply.configure()
        supply_voltage = ina_supply.voltage()
        supply_current = ina_supply.current()
        supply_power = ina_supply.power()
        
        supply = {}
        supply['voltage'] = supply_voltage
        supply['current'] = supply_current
        supply['power'] = supply_power
        
        if args.raw:
            print("Raspberry Pi power supply voltage: %.3f V" % supply_voltage)
            print("Current current consumption of Raspberry Pi: %.3f mA" % supply_current)
            print("Current power consumption of Raspberry Pi: %.3f mW" % supply_power)
        if args.influxdb:
            influxdb_publish('supply', supply);


#----------------
def publish_battery_data():
        ina_batt = INA219(0.005, busnum=DEVICE_BUS, address=0x45)
        ina_batt.configure()
        batt_voltage = ina_batt.voltage()
        batt_current = ina_batt.current()
        batt_power = ina_batt.power()
        
        battery = {}
        battery['voltage'] = batt_voltage
        battery['current'] = batt_current
        battery['power'] = batt_power
        
        if args.raw:
                print("Batteries Voltage: %.3f V" % batt_voltage)
                try:
                    if batt_current > 0:
                        print("Battery current (charging), rate: %.3f mA" % batt_current)
                        print("Current battery power supplement: %.3f mW" % batt_power)
                    else:
                        print("Battery current (discharge), rate: %.3f mA" % batt_current)
                        print("Current battery power consumption: %.3f mW" % batt_power)
                except DeviceRangeError:
                    print('Battery power is too high.')
                    
        if args.influxdb:
            influxdb_publish('battery', battery);
            
#----------------
def publish_device_data():
    bus = smbus2.SMBus(DEVICE_BUS)

    aReceiveBuf = []
    aReceiveBuf.append(0x00)   # Placeholder

    for i in range(1,255):
        aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))
        
    current_voltage_data = {}
    current_voltage_data['processor'] = (aReceiveBuf[2] << 8 | aReceiveBuf[1])
    current_voltage_data['Raspberry_Pi_reported'] = (aReceiveBuf[4] << 8 | aReceiveBuf[3])
    current_voltage_data['Battery_port_reported'] = (aReceiveBuf[6] << 8 | aReceiveBuf[5]) # This value is inaccurate during charging
    current_voltage_data['Charging_interface_(Type_C)'] = (aReceiveBuf[8] << 8 | aReceiveBuf[7])
    current_voltage_data['Charging_interface_(Micro_USB)'] = (aReceiveBuf[10] << 8 | aReceiveBuf[9])
    if args.influxdb:
        influxdb_publish('current_voltage_data', current_voltage_data);
    
    battery_data = {}
    battery_data['Temperature'] = (aReceiveBuf[12] << 8 | aReceiveBuf[11])
    battery_data['Full_voltage'] = (aReceiveBuf[14] << 8 | aReceiveBuf[13])
    battery_data['Empty_voltage'] = (aReceiveBuf[16] << 8 | aReceiveBuf[15])
    battery_data['Protection_voltage'] = (aReceiveBuf[18] << 8 | aReceiveBuf[17])
    battery_data['Remaining_capacity'] = (aReceiveBuf[20] << 8 | aReceiveBuf[19])
    if args.influxdb:
        influxdb_publish('battery_data', battery_data);
        
    device_data = {}
    device_data['Sampling'] = (aReceiveBuf[22] << 8 | aReceiveBuf[21])
    device_data['Power_state'] = aReceiveBuf[23]
    device_data['Shutdown_timer'] = (aReceiveBuf[24])
    device_data['Turn_on_with_power'] = (aReceiveBuf[25])
    device_data['Restart_timer'] = aReceiveBuf[26]
    device_data['Running_time'] = (aReceiveBuf[31] << 24 | aReceiveBuf[30] << 16 | aReceiveBuf[29] << 8 | aReceiveBuf[28])
    device_data['Charge_time'] = (aReceiveBuf[35] << 24 | aReceiveBuf[34] << 16 | aReceiveBuf[33] << 8 | aReceiveBuf[32])
    device_data['Uptime'] = (aReceiveBuf[39] << 24 | aReceiveBuf[38] << 16 | aReceiveBuf[37] << 8 | aReceiveBuf[36])
    device_data['Firmware'] = (aReceiveBuf[41] << 8 | aReceiveBuf[40])
    if args.influxdb:
        influxdb_publish('device_data', device_data);
        
    if args.raw:
        print("Current processor voltage: %d mV"% (aReceiveBuf[2] << 8 | aReceiveBuf[1]))
        print("Current Raspberry Pi report voltage: %d mV"% (aReceiveBuf[4] << 8 | aReceiveBuf[3]))
        print("Current battery port report voltage: %d mV"% (aReceiveBuf[6] << 8 | aReceiveBuf[5])) # This value is inaccurate during charging
        print("Current charging interface report voltage (Type C): %d mV"% (aReceiveBuf[8] << 8 | aReceiveBuf[7]))
        print("Current charging interface report voltage (Micro USB): %d mV"% (aReceiveBuf[10] << 8 | aReceiveBuf[9]))

        if (aReceiveBuf[8] << 8 | aReceiveBuf[7]) > 4000:
            print('Currently charging through Type C.')
        elif (aReceiveBuf[10] << 8 | aReceiveBuf[9]) > 4000:
            print('Currently charging via Micro USB.')
        else:
            print('Currently not charging.')   # Consider shutting down to save data or send notifications
    
        print("Current battery temperature (estimated): %d degC"% (aReceiveBuf[12] << 8 | aReceiveBuf[11])) # Learned from the battery internal resistance change, the longer the use, the more stable the data.
        print("Full battery voltage: %d mV"% (aReceiveBuf[14] << 8 | aReceiveBuf[13]))
        print("Battery empty voltage: %d mV"% (aReceiveBuf[16] << 8 | aReceiveBuf[15]))
        print("Battery protection voltage: %d mV"% (aReceiveBuf[18] << 8 | aReceiveBuf[17]))
        print("Battery remaining capacity: %d %%"% (aReceiveBuf[20] << 8 | aReceiveBuf[19]))  # At least one complete charge and discharge cycle is passed before this value is meaningful.
        print("Sampling period: %d Min"% (aReceiveBuf[22] << 8 | aReceiveBuf[21]))
        if aReceiveBuf[23] == 1:
            print("Current power state: normal")
        else:
            print("Current power status: off")

        if aReceiveBuf[24] == 0:
            print('No shutdown countdown!')
        else:
            print("Shutdown countdown: %d sec"% (aReceiveBuf[24]))

        if aReceiveBuf[25] == 1:
            print("Automatically turn on when there is external power supply!")
        else:
            print("Does not automatically turn on when there is an external power supply!")
        if aReceiveBuf[26] == 0:
            print('No restart countdown!')
        else:
            print("Restart countdown: %d sec"% (aReceiveBuf[26]))

        print("Accumulated running time: %d sec"% (aReceiveBuf[31] << 24 | aReceiveBuf[30] << 16 | aReceiveBuf[29] << 8 | aReceiveBuf[28]))
        print("Accumulated charged time: %d sec"% (aReceiveBuf[35] << 24 | aReceiveBuf[34] << 16 | aReceiveBuf[33] << 8 | aReceiveBuf[32]))
        print("This running time: %d sec"% (aReceiveBuf[39] << 24 | aReceiveBuf[38] << 16 | aReceiveBuf[37] << 8 | aReceiveBuf[36]))
        print("Version number: %d "% (aReceiveBuf[41] << 8 | aReceiveBuf[40]))

# Serial Number
        UID0 = "%08X" % (aReceiveBuf[243] << 24 | aReceiveBuf[242] << 16 | aReceiveBuf[241] << 8 | aReceiveBuf[240])
        UID1 = "%08X" % (aReceiveBuf[247] << 24 | aReceiveBuf[246] << 16 | aReceiveBuf[245] << 8 | aReceiveBuf[244])
        UID2 = "%08X" % (aReceiveBuf[251] << 24 | aReceiveBuf[250] << 16 | aReceiveBuf[249] << 8 | aReceiveBuf[248])
        print("Serial number: " + UID0 + "-" + UID1 + "-" + UID2 )
        
#----------------
if __name__ == "__main__":

    # argument parsing is u.g.l.y it ain't got no alibi, it's ugly !
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        """,
    )

    parser.add_argument("-r", "--raw",     dest="raw",     action="store_true", help="Print data to stddout")

    parser.add_argument("--influxdb",      dest="influxdb",      action="store_true",                                 help="publish to influxdb")
    parser.add_argument("--influxdb_host", dest="influxdb_host", action="store",      default="localhost",            help="hostname of InfluxDB HTTP API")
    parser.add_argument("--influxdb_port", dest="influxdb_port", action="store",      default=8086,         type=int, help="hostname of InfluxDB HTTP API")
    parser.add_argument("--influxdb_user", dest="influxdb_user", action="store",                                      help="InfluxDB username")
    parser.add_argument("--influxdb_pass", dest="influxdb_pass", action="store",                                      help="InfluxDB password")
    parser.add_argument("--influxdb_db",   dest="influxdb_db",   action="store",      default="upsplus",              help="InfluxDB database name")

    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="verbose mode")

    args = parser.parse_args()

    try:
        publish_raspberry_pi_data()
        publish_battery_data()
        publish_device_data()
    except Exception as e:
        print("Failed to fetch data: %s" % e)

