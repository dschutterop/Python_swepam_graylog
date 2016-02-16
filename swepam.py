#!/usr/bin/env python
#
# = Synopsis
# Hugely inspired by Lennart Koopmann's Graylog Spaceweather plugin
# https://marketplace.graylog.org/addons/8adb2876-bdd6-4163-8a39-f218086f6cde
#
# I can't connect directly to the web and must use a proxy,
# Since I can't get Lennart's plugin to work without ploughing through
# his code, I just built a very straightforward-errors-be-damned Python
# version of the plugin.
#
# Lennart described his plugin waaaay better, so here's what he has to say:
#
# (This is not actually providing any value at all - except fun and the
# possibility to decently nerd out )
#
# This Graylog input plugin reads data from the Advanced Composition Explorer (ACE)
# spacecraft which was launched in 1997 and is positioned at the so called L1
#  Lagrangian point where the gravity attraction of the Sun counters the
# gravity attraction of Earth.
#
# Together with several other missions, the ACE spacecraft is sitting there and
# constantly recording metrics about the stuff that the Sun is throwing out in
# the direction of the Earth using the Solar Wind Electron, Proton and Alpha
# Monitor (SWEPAM). This plugin is reading data from SWEPAM.
#
# == What.
# Yes. You can now correlate your system health with solar activity and
# geomagnetic storms. Ever needed a proof that a solar storm made a bit
# flip and your systems crash? Now you can! Correlate proton density to
# the response time of your app and the ion temperature to your exception rate.
# 500% more useful on dashboards!
#
#
# Author  : D. Schutterop <daniel@schutterop.nl>
# Date    : 11-02-2016
# Version : v0.2
#
# == Changelog
# 16-02-2016 : Added Graphite section to be able to log to Graylog
#              and Graphite at once.
#
#
import urllib2
import json
import socket
import time
import sys
import os

logToGraylog    = True
spaceWeatherURL = 'http://services.swpc.noaa.gov/text/ace-swepam.txt'
grayLogURL      = 'http://graylog.localdomain:12201/gelf'

logToGraphite   = True
grpHost         = 'graphite.localdomain'
grpPort         = 2003
grpDatabase     = 'swepam'

runInterval     = 60


def protonDensityCode(arg):
  if arg == -9999.9:
    return 0
  else:
    return arg

def swbsCode(arg):
  if arg == -9999.9:
    return 0
  else:
    return arg

def ionTemperatureCode(arg):
  if arg == -100000.0:
    return 0
  else:
    return arg

def getSpaceWeather(url):
  try:
    spaceWeatherRequest = urllib2.urlopen(spaceWeatherURL)
  except urllib2.URLError, (error):
    print ("Error opening %s:%s" % (spaceWeatherURL,error) )
    exit(99)


  weatherLine    = {}
  weatherElement = {}

  i = 0
  for line in spaceWeatherRequest:
    line = line.decode()
    weatherLine[i] = line
    i += 1

  targetLine = weatherLine[len(weatherLine)-1]

  i = 0
  for element in targetLine.split():
    weatherElement[i] = element
    i += 1

  return weatherElement

def pushToGraylog(gelfData):

  try:
    graylogRequest = urllib2.Request(grayLogURL, gelfData, {'Content-Type': 'application/json'})
    graylogPush = urllib2.urlopen(graylogRequest)
    graylogResponse = graylogPush.read()
    graylogPush.close()

  except urllib2.URLError, (error):
    print("Error opening %s:%s" % (grayLogURL,error))
    exit(99)

def pushToGraphite(gelfData):
  grpSocket = socket.socket()
  grpSocket.connect((grpHost,grpPort))

  message = ''
  graphiteData = json.loads(gelfData)
  for listItem in graphiteData:
    if isinstance(graphiteData[listItem],float):
      message = "\n %s %s" % (grpPutMessage(listItem,graphiteData[listItem]),message)

  message = "%s \n" % (message)
  grpSocket.sendall(message)
  grpSocket.close()


def grpPutMessage(grpMetricKey,grpMetricValue):
  metricPrepend = grpDatabase
  metricAppend  = grpMetricKey
  metricKey     = "%s.%s" % (metricPrepend,grpMetricKey)
  metricTime    = int(time.time())

  metricValue   = grpMetricValue

  return "%s %s %s" % (metricKey,metricValue,metricTime)

def main(runInterval):
  while True:
    weatherElement = getSpaceWeather(spaceWeatherURL)

    weatherDateYear       = int(weatherElement[0])
    weatherDateMonth      = int(weatherElement[1])
    weatherDateDay        = int(weatherElement[2])
    weatherDateTime       = int(weatherElement[3])
    weatherDateJulian     = int(weatherElement[4])
    weatherDateSeconds    = int(weatherElement[5])
    weatherStatus         = int(weatherElement[6])
    weatherProtonDensity  = protonDensityCode(float(weatherElement[7]))
    weatherSWBSpeed       = swbsCode(float(weatherElement[8]))
    weatherIonTemperature = ionTemperatureCode(float(weatherElement[9]))

    data = {}
    data['short_message']                = "Space Weather (%d/%d/%d)" % (weatherDateMonth,weatherDateDay,weatherDateYear)
    data['host']                         = socket.gethostname()
    data['facility']                     = 'info'
    data['satellite']                    = 'ace'
    data['instrument']                   = 'swepam'
    data['swepam_julian']                = weatherDateJulian
    data['swepam_year']                  = weatherDateYear
    data['swepam_month']                 = weatherDateMonth
    data['swepam_day']                   = weatherDateDay
    data['swepam_time']                  = weatherDateTime
    data['swepam_status_code']           = weatherStatus
    data['swepam_proton_density']        = weatherProtonDensity
    data['swepam_solar_wind_bulk_speed'] = weatherSWBSpeed
    data['swepam_ion_temperature']       = weatherIonTemperature

    data = json.dumps(data)

    if logToGraylog == True:
      pushToGraylog(data)

    if logToGraphite == True:
      pushToGraphite(data)

    time.sleep(runInterval)

if __name__ == "__main__":
  procPid = os.fork()

  if procPid != 0:
    sys.exit(0)

  print ("Running %s every %s seconds in the background." % (__file__,runInterval))

main(runInterval)
