# The code is based on the cwxn (Cumulus WXNow) interface by Matthew Wall.
# Distributed under terms of the GPLv3
"""
weewxAprx - APRX ready output file

weewx-aprx is an extension for weewx which produces a file which can be
feed directly into aprx. 

[weewxAprx]
    filename = /var/tmp/aprx_wx.txt
    binding = loop
    symbol = /_
    note = ""
    position = true

[Engine]
    [[Services]]
        process_services = ..., user.aprx.weewxAprx
"""
import time

import weewx
import weewx.wxformulas
import weeutil.weeutil
import weeutil.Sun
from weewx.engine import StdService

try:
    # WeeWX4 logging
    import logging
    from weeutil.logger import log_traceback

    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)

    def log_traceback_error(prefix=''):
        log_traceback(log.error, prefix=prefix)

except ImportError:
    # WeeWX legacy (v3) logging via syslog
    import syslog
    from weeutil.weeutil import log_traceback

    def logmsg(level, msg):
        syslog.syslog(level, 'weewxAprx: %s' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)

    def log_traceback_error(prefix=''):
        log_traceback(prefix=prefix, loglevel=syslog.LOG_ERR)

VERSION = "0.5"

def convert(v, metric, group, from_unit_system, to_units):
    ut = weewx.units.getStandardUnitType(from_unit_system, metric)
    vt = (v, ut[0], group)
    v = weewx.units.convert(vt, to_units)[0]
    return v


def nullproof(key, data):
    if key in data and data[key] is not None:
        return data[key]
    return 0


def calcRainHour(dbm, ts):
    sts = ts - 3600
    val = dbm.getSql("SELECT SUM(rain) FROM %s "
                     "WHERE dateTime>? AND dateTime<=?" % dbm.table_name,
                     (sts, ts))
    if val is None:
        return None
    return val[0]


def calcRain24(dbm, ts):
    sts = ts - 86400
    val = dbm.getSql("SELECT SUM(rain) FROM %s "
                     "WHERE dateTime>? AND dateTime<=?" % dbm.table_name,
                     (sts, ts))
    if val is None:
        return None
    return val[0]


def calcDayRain(dbm, ts):
    sts = weeutil.weeutil.startOfDay(ts)
    val = dbm.getSql("SELECT SUM(rain) FROM %s "
                     "WHERE dateTime>? AND dateTime<=?" % dbm.table_name,
                     (sts, ts))
    if val is None:
        return None
    return val[0]


class weewxAprx(StdService):

    def __init__(self, engine, config_dict):
        super(weewxAprx, self).__init__(engine, config_dict)
        loginf("service version is %s" % VERSION)
        d = config_dict.get('weewxAprx', {})
        self.note = d.get('note',{})
        self.symbol = d.get('symbol','/_')
        self.filename = d.get('filename', '/var/tmp/aprx_wx.txt')
        position = d.get('position', 'true').lower()
        if position == 'true':
            self.latitude = ''.join(weeutil.weeutil.latlon_string(
                self.engine.stn_info.latitude_f,
                ('N', 'S'), 'lat'))
            self.longitude = ''.join(weeutil.weeutil.latlon_string(
                self.engine.stn_info.longitude_f,
                ('E', 'W'), 'lon'))
        else:
            self.latitude = None
            self.longitude = None
        binding = d.get('binding', 'loop').lower()
        if binding == 'loop':
            self.bind(weewx.NEW_LOOP_PACKET, self.handle_new_loop)
        else:
            self.bind(weewx.NEW_ARCHIVE_RECORD, self.handle_new_archive)
        loginf("binding is %s" % binding)
        loginf("output goes to %s" % self.filename)

    def handle_new_loop(self, event):
        self.handle_data(event.packet)

    def handle_new_archive(self, event):
        self.handle_data(event.record)

    def handle_data(self, event_data):
        try:
            dbm = self.engine.db_binder.get_manager('wx_binding')
            data = self.calculate(event_data, dbm)
            self.write_data(data)
        except Exception as e:
            log_traceback_error('weewxAprx: **** ')

    def calculate(self, packet, archive):
        pu = packet.get('usUnits')
        data = dict()
        data['dateTime'] = packet['dateTime']
        data['windDir'] = nullproof('windDir', packet)
        v = nullproof('windSpeed', packet)
        data['windSpeed'] = convert(v, 'windSpeed', 'group_speed', pu, 'mile_per_hour')
        v = nullproof('windGust', packet)
        data['windGust'] = convert(v, 'windGust', 'group_speed', pu, 'mile_per_hour')
        v = nullproof('outTemp', packet)
        data['outTemp'] = convert(v, 'outTemp', 'group_temperature', pu, 'degree_F')
        v = calcRainHour(archive, data['dateTime'])
        if v is None:
            v = 0
        data['hourRain'] = convert(v, 'rain', 'group_rain', pu, 'inch')
        if 'rain24' in packet:
            v = nullproof('rain24', packet)
        else:
            v = calcRain24(archive, data['dateTime'])
            v = 0 if v is None else v
        data['rain24'] = convert(v, 'rain', 'group_rain', pu, 'inch')
        if 'dayRain' in packet:
            v = nullproof('dayRain', packet)
        else:
            v = calcDayRain(archive, data['dateTime'])
            v = 0 if v is None else v
        data['dayRain'] = convert(v, 'rain', 'group_rain', pu, 'inch')
        data['outHumidity'] = nullproof('outHumidity', packet)
        v = nullproof('barometer', packet)
        data['barometer'] = convert(v, 'pressure', 'group_pressure', pu, 'mbar')
        return data

    def write_data(self, data):
        fields = []
        if self.latitude is not None:
            fields.append("%s" % self.latitude)
            fields.append("%s" % self.symbol[0])
            fields.append("%s" % self.longitude)
            fields.append("%s" % self.symbol[1])
        fields.append("%03d" % int(data['windDir']))
        fields.append("/%03d" % int(data['windSpeed']))
        fields.append("g%03d" % int(data['windGust']))
        fields.append("t%03d" % int(data['outTemp']))
        fields.append("r%03d" % int(data['hourRain'] * 100))
        fields.append("p%03d" % int(data['rain24'] * 100))
        fields.append("P%03d" % int(data['dayRain'] * 100))
        if data['outHumidity'] < 0 or 100 <= data['outHumidity']:
            data['outHumidity'] = 0
        fields.append("h%03d" % int(data['outHumidity']))
        fields.append("b%05d" % int(data['barometer'] * 10))
        fields.append("%s" % self.note)
        with open(self.filename, 'w') as f:
            f.write(time.strftime("@%d%H%Mz",
                                  time.localtime(data['dateTime'])))
            f.write(''.join(fields))
            f.write("\n")
