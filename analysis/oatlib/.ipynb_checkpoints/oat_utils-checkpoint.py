# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division


# from datetime import datetime, timedelta
try:
    from pandas.tseries.resample import TimeGrouper
except:
    from pandas.core.resample import TimeGrouper
import pandas as pd
import numpy as np
import isodate
from datetime import datetime, tzinfo, timedelta
from functools import reduce


def read_dis(disc):
    """ read a MODFLOW discretzation file """

    with open(disc) as fp:
        lines = fp.readlines()

        # skip set0 & comments
        l = 0
        while lines[l][0] == "#":
            l += 1

        # dataset1
        set1 = lines[l][:lines[l].find("#")].split()
        l += 1
        NLAY = int(set1[0])
        NROW = int(set1[1])
        NCOL = int(set1[2])
        NPER = int(set1[3])
        ITMUNI = int(set1[4])
        LENUNI = int(set1[5])

        # skip set0 & comments
        while lines[l][0] == "#":
            l += 1

        # dataset2
        set2 = lines[l][:lines[l].find("#")].split()
        l += 1
        LAYCB = int(set2[0])

        # skip set0 & comments
        while lines[l][0] == "#":
            l += 1

        # dataset3
        DELR = None
        matrix = []
        if lines[l].find("CONSTANT") >= 0:
            DELR = int(float(lines[l][:lines[l].find("#")].split()[-1]))
            l += 1
        elif lines[l].find("EXTERNAL") >= 0 or lines[l].find("OPEN/CLOSE") >= 0:
            l += 1  # this is not implemented, just skipped
        else:  # includes with or without INTERNAL in format line
            if lines[l].find("INTERNAL") >= 0:
                l += 1
            while DELR is None:
                matrix += lines[l][:lines[l].find("#")].split()
                l += 1
                if len(matrix) >= NCOL:
                    DELR = matrix

        # skip set0 & comments
        while lines[l][0] == "#":
            l += 1

        # dataset4
        DELC = None
        matrix = []
        if lines[l].find("CONSTANT") >= 0:
            DELC = int(float(lines[l][:lines[l].find("#")].split()[-1]))
            l += 1
        elif lines[l].find("EXTERNAL") >= 0 or lines[l].find("OPEN/CLOSE") >= 0:
            l += 1  # this is not implemented, just skipped
        else:  # includes with or without INTERNAL in format line
            if lines[l].find("INTERNAL") >= 0:
                l += 1
            while DELC is None:
                matrix += lines[l][:lines[l].find("#")].split()
                l += 1
                if len(matrix) >= NROW:
                    DELC = matrix

        # skip set0 & comments
        while lines[l][0] == "#":
            l += 1

        # dataset5
        TOP = None
        matrix = []
        if lines[l].find("CONSTANT") >= 0:
            TOP = int(lines[l][:lines[l].find("#")].split()[-1])
            l += 1
        elif lines[l].find("EXTERNAL") >= 0 or lines[l].find("OPEN/CLOSE") >= 0:
            l += 1  # this is not implemented, just skipped
        else:
            if lines[l].find("INTERNAL") >= 0:
                l += 1
            while TOP is None:
                matrix += lines[l][:lines[l].find("#")].split()
                l += 1
                if len(matrix) >= NCOL * NROW:
                    TOP = matrix

        # skip set0 & comments
        while lines[l][0] == "#":
            l += 1

        # dataset6
        BOTM = [None] * (NLAY + LAYCB)
        for i in range(NLAY + LAYCB):
            matrix = []
            if lines[l].find("CONSTANT") >= 0:
                BOTM[i] = int(lines[l][:lines[l].find("#")].split()[-1])
                l += 1
            elif lines[l].find("EXTERNAL") >= 0 or lines[l].find("OPEN/CLOSE") >= 0:
                l += 1  # this is not implemented, just skipped
            else:
                if lines[l].find("INTERNAL") >= 0:
                    l += 1
                while BOTM[i] is None:
                    matrix += lines[l][:lines[l].find("#")].split()
                    l += 1
                    if len(matrix) >= NCOL * NROW:
                        BOTM[i] = matrix

            # skip set0 & comments
            while lines[l][0] == "#":
                l += 1

        # dataset7
        set7 = []  # stress periods length index 0 = SP1
        while l < len(lines):
            set7.append(lines[l][:lines[l].find("#")].split())
            l += 1
        set7c = zip(*set7)

        # print("====")
        # print(set7)
        # print("====")
        # print(set7c)
        # print("====")

        PERLEN = [float(a) for a in set7c[0]]
        NSTP = [int(a) for a in set7c[1]]
        TSMULT = [float(a) for a in set7c[2]]
        SSTR = set7c[3]

        # print(PERLEN)
        return PERLEN


def get_startdate(startdate):
    """ convert start date from text to datetime object """
    try:
        ts_parse = datetime.strptime(startdate, '%Y-%m-%dT%H:%M:%S.%fZ')
    except Exception as e:
        try:
            import dateutil.parser
            ts_parse = dateutil.parser.parse(startdate).replace(tzinfo=None)
        except Exception as e:
            raise Exception("'startdate' input value is not correct")
    return ts_parse


def sensors_to_istsos(service, procedure, obspro_sensor, offering="temporary",
                      temporalFilter=None, basic_auth=None,
                      qualityIndex=True, nan_qi=0, how_merge='outer',
                      period=None, time_zone=None):

    """Merge sensors and load data to a procedure on an istsos server instance

    Args:
        service (str): url of the SOS service
        procedure (list): sensor name
        obspro_sensor (dict): dictionary of observed property definition key and OAT sensor value
                              - e.g.:
                              {'urn:x-def:ist:meteo:ait:temparature': trev1,
                               'urn:x-def:ist:meteo:ait:temparature:max': trev_max,}
        offering (str): name of the offering - default value is \'temporary\'
        basic_auth(tuple): touple of username and password - e.g.: ('utente','123')
        qualityIndex (bool): if True istSOS qualityIndex is uploaded to istSOS
        nan_qi (int): values to be used as quality index in case of null values
        how_merge (str): specific merge options: {'left', 'right', 'outer', inner}, default 'outer'
                   * left: use only keys from left frame (SQL: left outer join)
                   * right: use only keys from right frame (SQL: right outer join)
                   * outer: use union of keys from both frames (SQL: full outer join)
                   * inner: use intersection of keys from both frames (SQL: inner join)
       time_zone (str): the time-zone to apply to series, default is UTC or time-zone of first sensor
    """

    try:
        import requests
        import json
        # from io import StringIO
        import pandas as pd

    except ImportError:
        raise ImportError('<requests> package not installed')

    # prepare useful variables
    service = service.rstrip("/")
    url = "/".join(service.split("/")[:-1])
    instance = service.split("/")[-1]

    if basic_auth:
        if len(basic_auth) == 2:
            sos_auth = requests.auth.HTTPBasicAuth(
                basic_auth[0], basic_auth[1]
            )
        else:
            raise ValueError('<basic_auth> tuple numerosity is TWO')
    else:
        sos_auth = None

    # Load procedure description and get observedProperties & assignedSensorId
    ###########################################################################
    res = requests.get("%s/wa/istsos/services/%s/procedures/%s" % (
              url,
              instance,
              procedure
              ), auth=sos_auth, verify=False)
    try:
        data = res.json()
    except Exception as e:
        print(res.text)
        raise e

    if data['success'] is False:
        raise Exception(
            "Description of procedure %s can not be loaded: %s" % (
                procedure, data['message']
            )
        )

    data = data['data']

    aid = data['assignedSensorId']  # -> sensor id

    op = []  # -> observed properties
    for out in data['outputs']:
        if qualityIndex is True:
            op.append(out['definition'])
        elif ':qualityIndex' not in out['definition']:
            op.append(out['definition'])

    # Load a getobservation request
    ################################
    res = requests.get(
        (
            "%s/wa/istsos/services/%s/operations/getobservation/" +
            "offerings/%s/procedures/%s/observedproperties/%s/eventtime/last"
        ) %
        (
            url,
            instance,
            'temporary',
            procedure,
            ','.join(op)
        ), auth=sos_auth, verify=False)

    try:
        data = res.json()
    except Exception as e:
        print(res)
        raise e

    if data['success'] is False:
        raise Exception(
            "Last observation of procedure %s can not be loaded: %s" % (
                procedure, data['message']
            )
        )

    io_data = data['data'][0]

    jsonindex = {}  # definition:index dict in observation
    ordered_obs = []

    for pos, field in enumerate(io_data['result']['DataArray']['field']):
        if 'iso8601' not in field[
            'definition'] and ':qualityIndex' not in field[
                'definition']:
            ordered_obs.append(field['definition'])

        if 'iso8601' in field['definition']:
            jsonindex[field['definition']] = pos
        elif qualityIndex:
            jsonindex[field['definition']] = pos
        elif not qualityIndex and ':qualityIndex' not in field['definition']:
            jsonindex[field['definition']] = pos

    # Manipulate getObservation response to execute an insertObservation
    ######################################################################

    # Get instant of last observation & set measures to an empty array
    io_data['result']['DataArray']['values'] = []

    # adjust component
    io_comp = []
    for k in io_data['observedProperty']['component']:
        if k in list(jsonindex.keys()):
            io_comp.append(k)
    io_data['observedProperty']['component'] = io_comp

    # adjust len CompositePhenomenon
    io_data['observedProperty'][
        'CompositePhenomenon']['dimension'] = "%s" % len(jsonindex)

    # adjust DataArray fields
    io_data['result']['DataArray']['elementCount'] = "%s" % len(jsonindex)
    io_fields = []
    for k in io_data['result']['DataArray']['field']:
        if k['definition'] in list(jsonindex.keys()):
            io_fields.append(k)
    io_data['result']['DataArray']['field'] = io_fields

    # ordered_ts = [None]*int((len(jsonindex)))
    # the ordered list of time series
    # ordered_ts = [None]*int((len(jsonindex)-1)/2)
    # the ordered list of time series
    ordered_ts = []

    # Check Observed Properties are all avaiable &
    # prepare the list of time series to be merged
    for uri, pos in list(jsonindex.items()):
        if ('iso8601' not in uri) and (':qualityIndex' not in uri):
            if uri not in list(obspro_sensor.keys()):
                raise Exception(
                    (
                        "Mandatory observed property %s is not" +
                        " present in sensor list."
                    ) % uri
                )
    for o in ordered_obs:
        if o not in list(obspro_sensor.keys()):
            raise Exception(
                (
                    "Mandatory observed property %s is not" +
                    " present in sensor list."
                ) % uri
            )
        if qualityIndex:
            ordered_ts.append(obspro_sensor[o].ts[['data', 'quality']])
        else:
            ordered_ts.append(obspro_sensor[o].ts[['data']])

    # Merge the time series
    df_final = reduce(
        lambda left, right: pd.merge(
            left, right, left_index=True, right_index=True, how=how_merge
        ), ordered_ts
    )

    # print(df_final)

    # remove nan in df_final along quality index and convert qi column
    # to integer
    if qualityIndex:
        for c in df_final.columns.values:
            if "quality" in c:
                df_final[c].fillna(nan_qi, inplace=True)
                df_final[c] = df_final[c].astype(int)

    if time_zone is None:
        if obspro_sensor[list(obspro_sensor.keys())[0]].tz == 0:
            time_zone = "Z"
        else:
            time_zone = obspro_sensor[list(obspro_sensor.keys())[0]].tz

    # Set observations to be inserted
    io_data['result']['DataArray']['values'] = [
        f.split(",") for f in df_final.to_csv(
            header=False,
            na_rep=-999.9,
            date_format="%Y-%m-%dT%H:%M:%S" + time_zone).split("\n")
        ]

    if len(io_data['result']['DataArray']['values'][-1]) != len(jsonindex):
        io_data['result']['DataArray']['values'].pop()

    # Set sampling Time
    if not period:
        io_data["samplingTime"] = {
            # "beginPosition": isodate.parse_datetime(
            #     df_final.index.min().to_pydatetime().isoformat() + time_zone
            # ),
            # "endPosition": isodate.parse_datetime(
            #     df_final.index.max().to_pydatetime().isoformat() + time_zone
            # )
            "beginPosition": io_data['result']['DataArray']['values'][0][0],
            "endPosition": io_data['result']['DataArray']['values'][-1][0]
        }
    else:
        start, end = period.split("/")
        start = isodate.parse_datetime(start)
        end = isodate.parse_datetime(end)

        first = isodate.parse_datetime(
            df_final.index.min().to_pydatetime().isoformat() + time_zone
        )
        last = isodate.parse_datetime(
            df_final.index.max().to_pydatetime().isoformat() + time_zone
        )
        # df_final.index.max().to_pydatetime().astimezone(
        #     Zone(time_zone, False, 'GMT')
        # )

        io_data["samplingTime"] = {
            "beginPosition": (start if start <= first else first).isoformat(),
            "endPosition": (last if last > end else end).isoformat(),
        }

    # Send the insertObservation request
    res = requests.post(
        "%s/wa/istsos/services/%s/operations/insertobservation" % (
            url,
            instance
        ),
        auth=sos_auth,
        verify=False,
        data=json.dumps({
            "ForceInsert": "true",
            "AssignedSensorId": aid,
            "Observation": io_data
        })
    )

    # Debugging POST request
    # print(json.dumps({
    #         "ForceInsert": "true",
    #         "AssignedSensorId": aid,
    #         "Observation": io_data
    #     }))

    out = res.json()
    try:
        out = res.json()
    except Exception as e:
        print(res)
        raise e

    if out['success'] is False:
        raise Exception("Procedure %s - %s" % (procedure, out['message']))
    else:
        return True


def sensorStats(
        oat, stat='mean', frequency='D', qilist=None, min_obs=None,
        nan_data=np.nan, nan_qi=0, closed='left', label='left',
        column_name=None):

    try:
        aggregations = {
            'data': [stat, 'count'],
            'quality': 'min',
        }
        toat = oat.copy()
        if stat == 'mean':
            grouped = toat.ts.dropna(how='any').groupby(
                TimeGrouper(freq=frequency, closed=closed, label=label)
            ).agg(aggregations)
            col_list = ['data','count']
            df1 = pd.DataFrame(data=None, columns=col_list)
            for i in grouped:
                df1['data'] = grouped[(u'data', 'mean')]
                df1['count'] = grouped[(u'data', 'count')]
        else:
            grouped = toat.ts.dropna(how='any').groupby(
                TimeGrouper(freq=frequency, closed=closed, label=label)
            )
            col_list = list(toat.ts.columns.values)
            col_list.append(u'time')
            df1 = pd.DataFrame(data=None, columns=col_list)
            for i in grouped:
                df = i[1]
                df.loc[:, u'time'] = df.index
                if not df.empty:
                    if stat == 'max':
                        df1.loc[i[0]] = df.loc[df['data'].idxmax()]
                    else:
                        df1.loc[i[0]] = df.loc[df['data'].idxmin()]
            toat.ts = df1
    except Exception as e:
        raise e
    else:

        # extract only data & quality
        if stat == 'mean':
            toat.ts = df1[['data','count']]
        else:
            toat.ts = toat.ts[['data', 'quality', 'time']]
        if column_name:
            if stat == 'mean':
                toat.ts.rename(
                    inplace=True,
                    columns={
                        'data': column_name,
                        'count': '{}_COUNT'.format(column_name)
                    }
                )
            else:
                toat.ts.rename(
                    inplace=True,
                    columns={
                        'data': column_name, 'time': 'TIME_' + column_name
                    }
                )
        toat.freq = frequency

        return toat


def sensorAggregate(
        oat, aggregation='mean', frequency='D', qilist=None, min_obs=None,
        nan_data=np.nan, nan_qi=0, closed='left', label='left',
        column_name=None):
    """
    Aggregate OAT.sensor according specified parameters

        Args:
            oat (OAT.sensor): OAT.sensor object to be aggregated
            aggregation (str): specific aggregation options:
                               {'max', 'min', 'mean', 'count'}, default 'mean'
            qilist (list): list of quality Index values to select observations
                           used in aggregation
            min_obs (float): minumum number of non null values recorded in the
                             period to calculate the aggregation (note that
                             this percentage includes only valid
                             qualityIndexed measures)
            nan_data (float): value to assign in aggregation when no or
                              insufficient data are available
            nan_qi (int): value to assign in aggregation when no or
                          insufficient data are available,
            closed (str): which side of bin interval is closed:
                          {‘right’, ‘left’}, default 'left'
            label (str): which bin edge label to label bucket with:
                         {‘right’, ‘left’}, default 'left'
    """

    try:
        aggregations = {
            'num': 'count',
            'data': aggregation,
            'quality': 'min'
        }
        toat = oat.copy()

        toat.ts['num'] = 1

        if qilist:
            toat.ts = toat.ts[
                (
                    toat.ts['quality'].isin(qilist)
                    &
                    toat.ts['quality'].notnull()
                )
            ].groupby(
                TimeGrouper(freq=frequency, closed=closed, label=label)
            ).agg(aggregations)
        else:
            toat.ts = toat.ts.dropna(how='any').groupby(
                TimeGrouper(freq=frequency, closed=closed, label=label)
            ).agg(aggregations)
        toat_values = list(toat.ts.columns.values)

        if min_obs:
            if (toat.ts['num'][0] < min_obs):
                # assign null to non satisfactory
                # toat_values[toat_values.index("num")] = 0
                # toat_values[toat_values.index("data")] = nan_data
                # toat_values[toat_values.index("quality")] = nan_qi
                # toat.ts[toat.ts['num'] < min_obs] = toat_values
                raise Exception(
                    (
                        "The aggregation does not satisfy the minimum" +
                        " number of observations [%s]"
                    ) % (min_obs)
                )
    except Exception as e:
        raise e
    else:

        # extract only data & quality
        toat.ts = toat.ts[['data', 'quality']]
        if column_name:
            toat.ts.rename(
                inplace=True,
                columns={'data': column_name}
            )
        toat.freq = frequency

        return toat


class Zone(tzinfo):
    """
    Return the tzinfo associated with a string timezone offset - e.g.: '+02:30'
    Example: print datetime.now(Zone('-02:00',False,'GMT'))
    """
    def __init__(self, str_offset, isdst, name):
        """ """
        if str_offset and str_offset is not "Z":
            hm = str_offset.split(":")
            if len(hm) is 2:
                self.offset_h = int(str_offset.split(":")[0])
                self.offset_m = int(str_offset.split(":")[1])
            elif len(hm) is 1:
                self.offset_h = int(str_offset.split(":")[0])
                self.offset_m = 0
        else:
            self.offset_h = self.offset_m = 0
        self.isdst = isdst
        self.name = name

    def utcoffset(self, dt):
        """ """
        return timedelta(
            hours=self.offset_h, minutes=self.offset_m
        ) + self.dst(dt)

    def dst(self, dt):
        """ """
        return timedelta(hours=1) if self.isdst else timedelta(0)

    def tzname(self, dt):
        """ """
        return self.name
