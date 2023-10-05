![Github License](https://img.shields.io/github/license/dacarson/WeatherFlowApi) 

# RPi-UPSPlus-Exporter


## Description
Export [UPSPlus](https://wiki.52pi.com/index.php?title=EP-0136) data to Influx DB so that it can be graphed with Grafana. 

To be run as a cron job, do not run as a service. (If run in a loop, it will fail due to running out of file handles - SMBUS leaks handles)

Based on example scripts from ([UPSplus](https://github.com/geeekpi/upsplus/tree/main)) that show how to get all the detail from the device.

These five measurement tables are added to the database:
* Supply. This contains the voltage, current and power being supplied to the board.
* Battery. This contains the voltage, current and power of the battery.
* Current_voltage_data. This contains the voltage measurements read from the [registers](https://wiki.52pi.com/index.php?title=EP-0136#Register_Mapping).
* Battery_data. This contains details of the battery, eg remaining capacity, temperature, low voltage, full voltage, read from [registers](https://wiki.52pi.com/index.php?title=EP-0136#Register_Mapping).
* Device_data. This contains information about the board configurations and runtime retrieved from the [registers](https://wiki.52pi.com/index.php?title=EP-0136#Register_Mapping).

  
## Usage
```
usage: UPSPlus-exporter.py [-h] [-r] [--influxdb] [--influxdb_host INFLUXDB_HOST] [--influxdb_port INFLUXDB_PORT] 
                        [--influxdb_user INFLUXDB_USER] [--influxdb_pass INFLUXDB_PASS] [--influxdb_db INFLUXDB_DB] 
                        [-v]

optional arguments:
  -h, --help            show this help message and exit
  -r, --raw             print raw data to stddout
  --influxdb            publish to influxdb
  --influxdb_host INFLUXDB_HOST
                        hostname of InfluxDB HTTP API
  --influxdb_port INFLUXDB_PORT
                        hostname of InfluxDB HTTP API
  --influxdb_user INFLUXDB_USER
                        InfluxDB username
  --influxdb_pass INFLUXDB_PASS
                        InfluxDB password
  --influxdb_db INFLUXDB_DB
                        InfluxDB database name
  -v, --verbose         verbose mode
  ````

To configure as a cron job, `crontab -e`.
Recommend to run every 2 minutes, as that is the sampling interval of the battery status.

 `*/2 * * * * /usr/bin/python3 /home/pi/RPi-UPSPlus-Exporter/UPSPlus-exporter.py  --influxdb --influxdb_user logger --influxdb_pass pass`

  
  ## License

This content is licensed under [MIT License](https://opensource.org/license/mit/)
