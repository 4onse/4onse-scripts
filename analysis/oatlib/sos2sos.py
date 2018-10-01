# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

try:
    import sensor
    #import method
    #import oat_algorithms as oa
    import oat_utils as ou
    import requests
    #import json
    #from io import StringIO
    import pandas as pd

    import isodate

except ImportError as e:
    raise ImportError('required packages not installed %s' % e)

def istSOS2istSOS(from_istSOS, to_istSOS, to_sensors, gen_settings, verbose=False):
    """
    Proceed to transfer data from an istSOS instance to another istSOS instance,
    optionally applying data modification according to specifications

        Args:
            from_istSOS (dict): origin istSOS connection configurations - keys are:
                {
                    'service': 'http://istsos.org/istsos/demo',
                    'basic_auth': ('admin', 'admin')
                }'

            to_istSOS (dict): destination istSOS connection configurations - (see from_istsos)

            to_sensors (list): list of destination sensor with migration settings - keys are:
                {
                    'A_GNO_GNO': {
                        "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature": {
                            'origin_proc': 'P_TRE',
                            'origin_obspro': 'urn:ogc:def:parameter:x-istsos:1.0:meteo:air:rainfall',
                            'origin_agg_method': 'sum',
                            'origin_agg_freq': 'D',
                            'force_qi': 200
                            },
                        "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:rainfall":{
                            'origin_proc': 'T_TRE',
                            'origin_obspro': 'urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature',
                            'origin_agg_method': 'mean',
                            'origin_agg_freq': 'D'
                            }
                    },
                    'LOCARNO': {....}
                }
            settings (dict): general settings to be overridden in sensors["MYSENSOR"]["settings"]
    """

    # Set default settings
    def_settings = {
        'start_date': '1970-01-01T00:00:00',
        'forcePeriod': [],
        'updateQualityIndex': True,
        'filter_qilist': [],
        'min_obs': 1,
        'nan_qi': 0,
        'nan_data': -999.9,
        'closed': 'right',
        'label': 'right',
        'tz': '+00:00'
    }
    forcePeriod = False
    # Set general settings merging general into default
    for k in list(def_settings.keys()):
        if k in gen_settings:
            def_settings[k] = gen_settings[k]

    # Check origin istsos
    try:
        origin_service = from_istSOS['service'].rstrip("/")
    except:
        raise ValueError("to_istSOS['service'] is mandatory")

    origin_url = "/".join(origin_service.split("/")[:-1])
    origin_instance = origin_service.split("/")[-1]

    if from_istSOS['basic_auth']:
        if len(from_istSOS['basic_auth']) == 2:
            origin_auth = from_istSOS['basic_auth']
        else:
            raise ValueError('<basic_auth> tuple numerosity is TWO')
    else:
        origin_auth = None

    # Check destination istsos
    try:
        destination_service = to_istSOS['service'].rstrip("/")
    except:
        raise ValueError("to_istSOS['service'] is mandatory")

    destination_url = "/".join(destination_service.split("/")[:-1])
    destination_instance = destination_service.split("/")[-1]

    if to_istSOS['basic_auth']:
        if len(to_istSOS['basic_auth']) == 2:
            destination_auth = to_istSOS['basic_auth']
        else:
            raise ValueError('<basic_auth> tuple numerosity is TWO')
    else:
        destination_auth = None

    # set endposition of all observed sensors
    res = requests.get("%s/wa/istsos/services/%s/procedures/operations/getlist" % (
              destination_url,
              destination_instance
              ), auth=destination_auth, verify=False)
    data = res.json()
    destination_sensor_lastobs = {}
    destination_sensor_firstobs = {}
    for p in data['data']:
        if p['samplingTime']['endposition']:
            destination_sensor_lastobs[p['name']] = isodate.parse_datetime(p['samplingTime']['endposition'])
            destination_sensor_firstobs[p['name']] = isodate.parse_datetime(p['samplingTime']['beginposition'])
        else:
            destination_sensor_lastobs[p['name']] = isodate.parse_datetime('1700-01-01T00:00:00Z')
            destination_sensor_firstobs[p['name']] = isodate.parse_datetime('2050-01-01T00:00:00Z')

    # foreach destination sensor
    for dest_sens, obs in list(to_sensors.items()):
        if verbose:
            print("Processing data to update %s procedure" % dest_sens)
        push = True

        # Set sensor settings merging sensor settings into general
        sen_settings = {}
        if 'settings' in obs:
            sen_settings = obs['settings']
            del obs['settings']

        settings = {}
        for k in list(gen_settings.keys()):
            if k in sen_settings:
                settings[k] = sen_settings[k]
            else:
                settings[k] = gen_settings[k]

        aggsens = {}
        for key, dest_proc in list(obs.items()):

            # set OAT.sensor from origin
            asen = sensor.Sensor.from_istsos(
                service=origin_service,
                procedure=dest_proc['origin_proc'],
                observed_property=dest_proc['origin_obspro'],
                basic_auth=origin_auth
            )
            if verbose:
                print("|")
                print("|----> %s oat.sensor created" % key.split(":")[-1])

            timezone = settings['tz'] if 'tz' in settings else 'Z'

            #first_origin_obs = isodate.parse_datetime(asen.data_availability[0] + timezone)
            last_origin_obs = isodate.parse_datetime(
                                asen.data_availability[1] + timezone)

            #first_dest_obs = destination_sensor_firstobs[dest_sens].astimezone(
                                        #ou.Zone(timezone, False, 'GMT'))
            last_dest_obs = destination_sensor_lastobs[dest_sens].astimezone(
                                        ou.Zone(timezone, False, 'GMT'))

            print("|----- last_origin_obs/last_dest_obs: %s/%s" %(last_origin_obs,last_dest_obs))
            
            # get time series from origin
            if 'forcePeriod' in settings and settings['forcePeriod']:
                forcePeriod = True
                if len(settings['forcePeriod'].split("/")) == 2:
                    period = settings['forcePeriod']
                else:
                    delta = isodate.parse_duration(settings['forcePeriod'])
                    period = "%s/%s" % (
                        last_dest_obs.isoformat(),
                        (last_origin_obs - delta).isoformat()
                    )

            else:
                if last_origin_obs > last_dest_obs:

                    start = isodate.parse_datetime(settings['start_date'] + timezone)
                    if not dest_proc['origin_agg_freq'][0].isdigit():
                        td_freq = pd.to_timedelta(str('1%s' %(dest_proc['origin_agg_freq'])))
                    else:
                        td_freq = pd.to_timedelta(dest_proc['origin_agg_freq'])
                    gap = int((last_origin_obs - start) / td_freq) * td_freq

                    last_origin_obs = start + gap
                    if verbose:
                        print("|----- start: %s" % start)
                        print("|----- td_freq: %s" % td_freq)
                        print("|----- gap: %s" % gap)
                        print("|----- last_origin_obs: %s" % last_origin_obs)

                    period = "%s/%s" % (
                        last_dest_obs.isoformat(),
                        last_origin_obs.isoformat(),
                    )
                    if verbose:
                        print("|----- period: %s" % period)
                else:
                    if verbose:
                        print("|----> %s destination end-position > source end-position" % key.split(":")[-1])
                    push = False
                    break

            if 'frequency' in dest_proc and dest_proc['frequency']:
                frequency = dest_proc['frequency']
            elif 'frequency' in settings:
                frequency = settings['frequency']
            else:
                frequency = None

            asen.ts_from_istsos(
                service=origin_service,
                procedure=dest_proc['origin_proc'],
                observed_property=dest_proc['origin_obspro'],
                event_time=period,
                freq=frequency,
                basic_auth=origin_auth
            )
            if verbose:
                print("|----> %s timeSerie uploaded" % key.split(":")[-1])
                #if (not asen.ts is None):
                #    print("|----> STATS")
                #    print("|----> %s" % asen.ts.describe())
                #    print("|----> DATA")
                #    print("|----> %s" % asen.ts)

            #print(asen)

            if (not asen.ts is None) and (not asen.ts.empty):
                # aggregate serie (only if dest_proc['origin_agg_method']
                if 'origin_agg_method' in dest_proc and 'origin_agg_freq' in dest_proc:
                    aggsens[key] = ou.sensorAggergate(
                                    asen,
                                    qilist=settings['filter_qilist'] if 'filter_qilist' in settings else None,
                                    min_obs=settings['min_obs'] if 'min_obs' in settings else None,
                                    aggregation=dest_proc['origin_agg_method'],
                                    frequency=dest_proc['origin_agg_freq'],
                                    closed=settings['closed'] if 'closed' in settings else 'right',
                                    label=settings['label'] if 'label' in settings else 'right'
                                )
                else:
                    aggsens[key] = asen

                if 'force_qi' in dest_proc and dest_proc['force_qi']:
                    aggsens[key].ts['quality'] = dest_proc['force_qi']

                #FILL NO DATA WITH PROVIDED VLUES
                aggsens[key].ts.fillna(settings['nan_data'])
                if verbose:
                    print("|----> %s timeSerie aggregated" % key.split(":")[-1])
            else:
                if verbose:
                    print("|----> %s timeSerie empty" % key.split(":")[-1])
                push=False

        # insert observations
        if push:
            res = ou.sensors_to_istsos(
                service=destination_service,
                procedure=dest_sens,
                obspro_sensor=aggsens,
                qualityIndex=settings['updateQualityIndex'] if 'updateQualityIndex' in settings else True,
                period=period if forcePeriod else None,
                basic_auth=destination_auth,
                nan_qi=settings['nan_qi'] if 'nan_qi' in settings else 0  # TODO: use this for settings or dict in obsepro
            )
            if verbose:
                print("|")
                print("%s procedure successfully updated" % dest_sens)
                print("=================================")
        else:
            if verbose:
                print("|")
                print("%s procedure not updated" % dest_sens)
                print("=================================")














"""


    sensors = {
                'CANOBBIO': {
                    "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature": {
                        'procedure': 'P_TRE',
                        'obs_pro': 'urn:ogc:def:parameter:x-istsos:1.0:meteo:air:rainfall',
                        'aggregate': 'sum',
                        'frequency': 'D'
                        },
                    "urn:ogc:def:parameter:x-istsos:1.0:meteo:air:rainfall": {
                        'procedure': 'T_TRE',
                        'obs_pro': 'urn:ogc:def:parameter:x-istsos:1.0:meteo:air:temperature',
                        'aggregate': 'mean',
                        'frequency': 'D'
                        }
                },
                {....}
            }

    from_istSOS = {
        'service': 'https://geoservice.ist.supsi.ch/psos/sos',
        'basic_auth': ('admin', 'wP5396Wu7dE6572q')
    }

    to_istSOS = {
        'service': 'http://istsos.org/istsos/demo',
        'basic_auth': ('admin', 'wP5396Wu7dE6572q')
    }

    settings = {
        'forcePeriod': [],
        'updateQualityIndex': True,
        'filter_qilist': [200, 210, 220, 230, 320, 330],
        'min_obs': 1,
        'nan_qi': 100,
        'nan_data': -999.9,
        'closed': 'right',
        'label': 'right',
        'tz': 'Z'
    }
"""
