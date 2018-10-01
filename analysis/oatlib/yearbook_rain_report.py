# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import pandas as pd
import numpy as np
import datetime as dt
from calendar import monthrange, isleap


class prec_repo():
    """ """

    def __init_info__(self):
        """ initialize info """
        self.info = {
            "name": None,
            "no": None,
            "coordinates": None,
            "altitude": None,
            "bacino": None
            }

    def __init_cy_daily_data__(self, year=None):
        """ initialize current year daily_data """
        if year:
            self.cy_daily_data = [
                [np.nan] * monthrange(year, x + 1)[1] for x in range(12)]
        else:
            self.cy_daily_data = [[] for x in range(12)]

    def __init_cy_monthly_stats__(self):
        """ initialize cy_monthly_stats """
        self.cy_monthly_stats = {
            "sum": [np.nan for x in range(12)],
            "max": [(np.nan, "") for x in range(12)],
            "rainy_days": [np.nan for x in range(12)],
            }

    def __init_cy_yearly_stats__(self):
        """ initialize cy_yearly_stats """
        self.cy_yearly_stats = {
            "sum": np.nan,
            "mean": np.nan,
            "min": np.nan,
            "max": np.nan,
            "rainy_days": np.nan
            }

    def __init_monthly_stats__(self):
        """ initialize monthly_stats """
        self.monthly_stats = {
            "from": np.nan,
            "to": np.nan,
            "mean": [np.nan for x in range(12)],
            "max_mon": [(np.nan, "") for x in range(12)],
            "min_mon": [(np.nan, "") for x in range(12)],
            "max_day": [(np.nan, "") for x in range(12)],
            "max_rainy_days": [(np.nan, "") for x in range(12)],
            "min_rainy_days": [(np.nan, "") for x in range(12)],
            "mean_rainy_days": [np.nan for x in range(12)]
            }

    def __init_yearly_stats__(self):
        """ initialize yearly stats """
        self.yearly_stats = {
            "mean": np.nan,
            "rainy_days": np.nan
            }

    def __init_annual_monthly_stats__(self):
        """ initialize annual stats of historic records"""
        self.annual_stats = {
            "yearly_max_series": [(np.nan, "") for x in range(12)],
            "yearly_ave_series": [(np.nan, "") for x in range(12)],
            "yearly_min_series": [(np.nan, "") for x in range(12)],
            "yearly_max_series": [(np.nan, "") for x in range(12)],

            }



    def __init__(self):
        """ """
        self.__name__ = "prec_repo"
        self.__init_info__()
        self.__init_cy_daily_data__()
        self.__init_cy_monthly_stats__()
        self.__init_cy_yearly_stats__()
        self.__init_monthly_stats__()
        self.__init_yearly_stats__()

    def __repr__(self):
        """ """
        rep = "info: %s\n" % self.info
        rep += "cy_daily_data: %s\n" % self.cy_daily_data
        rep += "cy_monthly_stats: %s\n" % self.cy_monthly_stats
        rep += "cy_yearly_stats: %s\n" % self.cy_yearly_stats
        rep += "monthly_stats: %s\n" % self.monthly_stats
        rep += "yearly_stats: %s\n" % self.yearly_stats
        return rep

    def set_info(self, oat, no=None, bacino=None, name=None):
        """ set basic info """
        self.info["coordinates"] = "%s / %s" % (int(oat.lat), int(oat.lon))
        self.info["altitude"] = oat.alt
        if bacino:
            self.info["bacino"] = bacino
        if no:
            self.info["no"] = no
        if name:
            self.info["name"] = name
        else:
            self.info["name"] = oat.desc

    def set_cy_daily_data(self, oat, year):
        """ set daily data """
        self.__init_cy_daily_data__(year)
        year = str(year)
        for index, row in oat.ts[year].iterrows():
            try:
                #print(index.month, index.day, row['data'])
                #self.cy_daily_data[index.month - 1].append(
                    #float("%.1f" % row['data'])
                    #)
                self.cy_daily_data[index.month - 1][index.day - 1] = float(
                    "%.1f" % row['data'])
            except:
                print(index.month, index.day)

    def set_cy_monthly_stats(self, oat, year, perc=None, qilist=[]):
        """ set current year monthly stats

            Args:
                oat (obj): oat sensor object
                year (int): year to calculate statistics
                perc (int): if defined percentage of data availability
                            with associated quality in qlist
                            requested to calculate statistics
                qilist (list): list of acceptable qualityIndex values
                            to calculate stistics
        """
        self.__init_cy_monthly_stats__()
        for m in range(12):
            t = "%s-%02d" % (year, m + 1)
            try:
                mm = oat.ts[t]
                #number of non null observations
                obsnum = mm['data'].count()

                #verify x% of data has quality in [a,b,c,d,..]
                ms = mm['data'].sum()
                mx = mm['data'].max()
                rd = mm[mm['data'] >= 1]['data'].count()
                if perc:
                    if (obsnum / monthrange(year, m + 1)[1]) * 100 < perc:
                        ms = np.nan
                        mx = np.nan
                        rd = np.nan

                if qilist:
                    if any(mm['quality'].isin(qilist) == False):
                        ms = np.nan
                        mx = np.nan
                        rd = np.nan

                self.cy_monthly_stats["sum"][m] = float("%.1f" % ms)
                self.cy_monthly_stats["max"][m] = (
                    float("%.1f" % mx),
                    ", ".join([str(i) for i in mm[mm['data'] == mx].index.day])
                )
                self.cy_monthly_stats["rainy_days"][m] = rd

            except KeyError:
                #print("Caught KeyError: {}".format(exc))
                self.cy_monthly_stats["sum"][m] = None
                self.cy_monthly_stats["max"][m] = (None, "")
                self.cy_monthly_stats["rainy_days"][m] = None
            except:
                print("Caught KeyError GENERIC")
                raise
            #self.cy_monthly_stats["rainy_days"][m] = oat.ts[t][oat.ts['data'] >= 1]['data'].count()

    def set_cy_yearly_stats(self, oat, year, perc=None, qilist=[]):
        """ set current year yearly stats

            Args:
                oat (obj): oat sensor object
                year (int): year to calculate statistics
                perc (int): if defined percentage of data availability
                            requested to calculate month statistics
                qilist (list): list of acceptable qualityIndex values to calculate stistics
        """

        self.__init_cy_yearly_stats__()
        year = str(year)

        sm = float("%.1f" % oat.ts[year]['data'].sum())
        mi = float("%.1f" % oat.ts[year]['data'].min())
        ma = float("%.1f" % oat.ts[year]['data'].max())
        me = float("%.1f" % oat.ts[year]['data'].mean())
        rd = oat.ts[year][oat.ts['data'] >= 1]['data'].count()

        if perc:
            #number of non null observations
            obsnum = oat.ts[year]['data'].count()
            if (obsnum / (365 + (1 * isleap(int(year))))) * 100 < perc:
                sm = np.nan
                rd = np.nan
        if qilist:
            if any(oat.ts[year]['quality'].isin(qilist) == False):
                sm = np.nan
                rd = np.nan

        self.cy_yearly_stats["sum"] = sm
        self.cy_yearly_stats["min"] = mi
        self.cy_yearly_stats["max"] = ma
        self.cy_yearly_stats["mean"] = me
        self.cy_yearly_stats["rainy_days"] = rd

    def set_monthly_stats(self, oat, perc=100, qilist=[], good_months_perc=70):
        """ set historic monthly stats

            Args:
                oat (obj): oat sensor object
                perc (int): if defined percentage of data availability
                        requested to calculate statistics
                qilist (list): list of acceptable qualityIndex values
                        to calculate stistics
                good_months_perc: percentage of good months
                        to calculate statistics
        """

        self.__init_monthly_stats__()
        #years = range(oat.period()[0].year, oat.period()[1].year)
        toat = oat.copy()
        toat.ts['year'] = toat.ts.index.year
        toat.ts['month'] = toat.ts.index.month

        #assign statistic period
        try:
            self.monthly_stats["from"] = dt.datetime.strptime(toat.data_availability[0], "%Y-%m-%dT%H:%M:%S.%fZ").year
            self.monthly_stats["to"] = dt.datetime.strptime(toat.data_availability[1], "%Y-%m-%dT%H:%M:%S.%fZ").year
        except ValueError:
            self.monthly_stats["from"] = dt.datetime.strptime(toat.data_availability[0], "%Y-%m-%dT%H:%M:%S").year
            self.monthly_stats["to"] = dt.datetime.strptime(toat.data_availability[1], "%Y-%m-%dT%H:%M:%S").year

        #precipitation monthly statistics
        for m in range(12):

            # all month m in all the years
            amm = toat.ts[toat.ts['month'] == m + 1]

            #select years with sufficient data quality (n. of qilist data >perc)
            yearlist = []
            
            for y in toat.ts['year'].unique():

                den = amm[
                        (amm['month'] == m + 1)
                        & (amm['year'] == y)
                    ].count()['data']

                if qilist:
                    num = amm[
                            (amm['month'] == m + 1)
                            & (amm['year'] == y)
                            & (amm['quality'].isin(qilist))
                        ].count()['data']
                else:
                     num = amm[
                            (amm['month'] == m + 1)
                            & (amm['year'] == y)
                        ].count()['data']

                if den>0:
                    a = num / den
                    if a > perc / 100:
                        yearlist.append(y)
            
            #====================
            # data in yearlist

            #if we have enough good months we calculate statistics
            if (len(yearlist) / len(toat.ts['year'].unique())) > (good_months_perc/100):

                mm = amm[amm['year'].isin(yearlist)]

                print("=============")
                print(mm+1)

                #monthly mean prec
                self.monthly_stats["mean"][m] = float("%.1f" % mm.groupby('year').sum()['data'].mean())

                #sum of month m for each year
                grouper = mm.groupby('year').sum()
                tm = grouper['data'].min()
                tmx = grouper['data'].max()

                #max monthly prec
                self.monthly_stats["max_mon"][m] = (
                    float("%.1f" % tmx),
                    ", ".join([str(i) for i in grouper[grouper['data'] == tmx].index.values])
                    )

                #min monthly prec
                self.monthly_stats["min_mon"][m] = (
                    float("%.1f" % tm),
                    ", ".join([str(i) for i in grouper[grouper['data'] == tm].index.values])
                    )

                #max daily prec
                mmax = mm['data'].max()
                self.monthly_stats["max_day"][m] = (
                    float("%.1f" % mmax),
                    ", ".join(["%s %s" % (i.day, i.year) for i in mm[mm['data'] == mmax].index])
                    )

                #print("mmax: ",mmax)
                
                #calculate time series of days with precipitation
                #grouper2 = mm[(mm['data'] >= 1)].groupby('year').count()
                
                n_rainydays = []            
                for y in yearlist:
                    print("YEAR %s" % y)
                    n_rainydays.append(
                        amm[
                            (amm['month'] == m + 1)
                            & (amm['year'] == y)
                            & (amm['data'] >= 1)
                        ].count()['data']
                    )
                
                #max num day with prec
                mmax = max(n_rainydays)
                self.monthly_stats["max_rainy_days"][m] = (
                    int(mmax),
                    ", ".join([str(yearlist[i]) for i,v in enumerate(n_rainydays) if v==mmax])
                    )
                
                #min num day with prec
                mmin = min(n_rainydays)
                self.monthly_stats["min_rainy_days"][m] = (
                    int(mmin),
                    ", ".join([str(yearlist[i]) for i,v in enumerate(n_rainydays) if v==mmin])
                    )
                
                #mean num day with prec
                mmean = sum(n_rainydays)/len(n_rainydays)
                self.monthly_stats["mean_rainy_days"][m] = float("%.1f" % mmean)
                
                """
                #calculate time series of days with or without precipitation
                grouper2 = mm[(mm['data'] >= 1)].groupby('year').count()
                #grouper2 = mm[(mm['data'] >= 1)].groupby('year').size()
                grouper2.index = [dt.datetime(d, m + 1, 1) for d in grouper2.index]
                print("GROUPER 2: month %s " %(m+1))
                print(grouper2)
                print("END GROUPER 2:")
                #grouper = grouper2.resample('A', how='max').fillna(0)
                grouper = grouper2.resample('A').max().fillna(0)

                #max num day with prec
                mmax = grouper['data'].max()
                self.monthly_stats["max_rainy_days"][m] = (
                    int(mmax),
                    ", ".join([str(i) for i in grouper[grouper['data'] == mmax].index.year])
                    )

                #min num day with prec
                mmin = grouper['data'].min()
                self.monthly_stats["min_rainy_days"][m] = (
                    int(mmin),
                    ", ".join([str(i) for i in grouper[grouper['data'] == mmin].index.year])
                    )
                #print("****MMMMM****")
                #print(m)
                #print(self.monthly_stats["min_rainy_days"][m])

                #mean num day with prec
                mmean = grouper['data'].mean()
                self.monthly_stats["mean_rainy_days"][m] = float("%.1f" % mmean)
                
                """
                #verify constraints
                """
                if perc:
                    #number of non null observations
                    obsnum = mm['data'].count()
                    inumdays = ((int(self.monthly_stats["to"]) - int(self.monthly_stats["from"]))+1) * monthrange(int(self.monthly_stats["to"]), m + 1)[1]

                    if (obsnum / inumdays) * 100 < perc:
                        print("*****PREC*****")
                        print(obsnum, inumdays, self.monthly_stats["to"], self.monthly_stats["from"], (obsnum / inumdays) * 100, perc)
                        self.monthly_stats["mean"][m] = np.nan
                        self.monthly_stats["max_mon"][m] = (np.nan, "")
                        self.monthly_stats["min_mon"][m] = (np.nan, "")
                        self.monthly_stats["max_day"][m] = (np.nan, "")
                        self.monthly_stats["max_rainy_days"][m] = (np.nan, "")
                        self.monthly_stats["min_rainy_days"][m] = (np.nan, "")
                        self.monthly_stats["mean_rainy_days"][m] = np.nan

                if qilist:
                    if any(mm['quality'].isin(qilist) == False):
                        print("*****QUAL*****")
                        self.monthly_stats["mean"][m] = np.nan
                        self.monthly_stats["max_mon"][m] = (np.nan, "")
                        self.monthly_stats["min_mon"][m] = (np.nan, "")
                        self.monthly_stats["max_day"][m] = (np.nan, "")
                        self.monthly_stats["max_rainy_days"][m] = (np.nan, "")
                        self.monthly_stats["min_rainy_days"][m] = (np.nan, "")
                        self.monthly_stats["mean_rainy_days"][m] = np.nan
                """

    def set_yearly_stats(self, oat, perc=None, qilist=[], good_years_perc=70, monthly_stats_bond=False):
        """ set historic yearly stats

            Args:
                oat (obj): oat sensor object
                perc (int): if defined percentage of data availability
                            requested to calculate statistics
                qilist (list): list of acceptable qualityIndex values
                            to calculate stistics
                good_years_perc: percentage of good years data availability
                            to calculate statistics
        """

        self.__init_yearly_stats__()
        toat = oat.copy()
        toat.ts['year'] = toat.ts.index.year

        #if we have calculated all the monthly_stats, then we can calculate yearly stats
        if (
                monthly_stats_bond is True
            ) and (
                (
                    np.nan in self.monthly_stats["mean"]
                ) or (
                    None in self.monthly_stats["mean"]
                )
            ):
            return
            #self.yearly_stats["mean"] = float(
                        #"%.1f" % toat.ts.groupby('year').sum()['data'].mean()
                        #)
            #self.yearly_stats["rainy_days"] = float(
                        #"%.1f" % toat.ts[
                                #toat.ts['data'] >= 1
                            #].groupby('year').count()['data'].mean()
                        #)

        if perc:
            #select years with sufficient data quality (n. of qilist data >perc)
            yearlist = []
            for y in toat.ts['year'].unique():
                num = toat.ts[
                        (toat.ts['year'] == y)
                        & (toat.ts['quality'].isin(qilist))
                    ].count()['data']
                den = toat.ts[
                        (toat.ts['year'] == y)
                    ].count()['data']
                a = num / den
                if a > perc / 100:
                    yearlist.append(y)

                #if we have enough good years we calculate statistics
                if (len(yearlist) / len(toat.ts['year'].unique())) > (
                    good_years_perc / 100):
                    
                    #precipitation yearly mean
                    #self.yearly_stats["rainy_days"] = sum(self.monthly_stats["mean_rainy_days"])
                    #self.yearly_stats["mean"] = sum(self.monthly_stats["mean"])
            
                    """
                    print("----------------")
                    print("%.1f" % toat.ts[toat.ts['year'].isin(yearlist)].groupby('year').sum()['data'].mean())
                    print("%s" % toat.ts[
                                (toat.ts['year'].isin(yearlist)) 
                                & (toat.ts['data'] >= 1)
                            ].groupby('year').count()
                        )
                    print(yearlist)
                            
                    """
                    self.yearly_stats["mean"] = float(
                        "%.1f" % toat.ts[toat.ts['year'].isin(yearlist)].groupby('year').sum()['data'].mean()
                        )
                    self.yearly_stats["rainy_days"] = float(
                        "%.1f" % toat.ts[
                                (toat.ts['year'].isin(yearlist))
                                & (toat.ts['data'] >= 1)
                            ].groupby('year').count()['data'].mean()
                        )
            

        else:
            self.yearly_stats["mean"] = float(
                        "%.1f" % toat.ts.groupby('year').sum()['data'].mean()
                        )
            self.yearly_stats["rainy_days"] = float(
                        "%.1f" % toat.ts[
                                toat.ts['data'] >= 1
                            ].groupby('year').count()['data'].mean()
                        )
