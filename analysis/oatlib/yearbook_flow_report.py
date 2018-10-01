# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import pandas as pd
import numpy as np
import scipy.stats as sp
import datetime as dt
from calendar import monthrange, isleap


class flow_repo(prec_repo):
    """ """

    def __init__(self):
        "initialize"
        super(flow_repo, self).__init__()

    def __init_info__(self):
        """ initialize info """
        self.info = {
            "no": None,
            "name": None,
            "location": None,
            "coordinates": None,
            "altitude": None,
            "bacino": None,
            "altmed": None,
            "surface": None,
            "gewiss": None
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
            "mean": [np.nan for x in range(12)],
            "max": [(np.nan, "") for x in range(12)],
            "min": [(np.nan, "") for x in range(12)],
            }

    def __init_cy_yearly_stats__(self):
        """ initialize cy_yearly_stats """
        self.cy_yearly_stats = {
            "mean": np.nan,
            "specific_flow": np.nan
            }

    def __init_monthly_stats__(self):
        """ initialize monthly_stats """
        self.monthly_stats = {
            "mean": [np.nan for x in range(12)],
            "max_col": [(np.nan, "") for x in range(12)],
            "min_pun": [(np.nan, "") for x in range(12)],
            "min_mean": [(np.nan, "") for x in range(12)],
            }

    def __init_yearly_stats__(self):
        """ initialize yearly stats """
        self.yearly_stats = {
            "mean_mag": (np.nan, ""),
            "mean": np.nan,
            "mean_min": (np.nan, "")
            }

    def __init_duration_stats(self):
        """ initialize duration stats"""
        self.duration_stats = {
            "days": [1,3,6,9,18,36,55,73,91,114,137,160,
                182,205,228,251,274,292,310,329,347,356,362,365],
            "cy": [np.nan for x in range(24)],
            "hist": [np.nan for x in range(24)],
            }

    def __repr__(self):

        rep = "info: %s\n" % self.cy_daily_data
        rep += "cy_daily_data: %s\n" % self.cy_daily_data
        rep += "cy_monthly_stats: %s\n" % self.cy_monthly_stats
        rep += "cy_yearly_stats: %s\n" % self.cy_yearly_stats
        rep += "monthly_stats: %s\n" % self.monthly_stats
        rep += "yearly_stats: %s\n" % self.yearly_stats
        rep += "duration_stats: %s\n" % self.duration_stats
        return rep

    def set_info(self, oat, no=None, bacino=None, location=None,
            altmed=None, surface=None, gewiss=None):
        """ set basic info """
        self.info["name"] = oat.desc
        self.info["coordinates"] = "%s / %s" % (int(oat.lat), int(oat.lon))
        self.info["altitude"] = oat.alt
        if bacino:
            self.info["bacino"] = bacino
        if no:
            self.info["no"] = no
        if location:
            self.info["location"] = location
        if altmed:
            self.info["altmed"] = altmed
        if surface:
            self.info["surface"] = surface
        if gewiss:
            self.info["gewiss"] = gewiss

    def set_cy_daily_data(self, oat, year):
        """ set daily data """
        self.__init_cy_daily_data__(year)
        year = str(year)
        for index, row in oat.ts[year].iterrows():
            try:
                #print(index.month, index.day, row['data'])
                #self.cy_daily_data[index.month - 1].append(
                    #float("%.2f" % row['data'])
                    #)
                self.cy_daily_data[index.month - 1][index.day - 1] = float(
                    "%.2f" % row['data'])
            except:
                print(index.month, index.day)

    def set_cy_monthly_stat(self, oatmean, oatmin, oatmax, year, perc=None, qilist=[]):
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
                mmean = oatmean.ts[t]
                mmin = oatmin.ts[t]
                mmax = oatmax.ts[t]

                #number of non null observations
                obsnum = mmean['data'].count()

                #verify x% of data has quality in [a,b,c,d,..]
                me = mmean['data'].mean()
                mx = mmax['data'].max()
                mn = mmin['data'].min()

                if perc:
                    if (obsnum / monthrange(year, m + 1)[1]) * 100 < perc:
                        me = np.nan
                        mx = np.nan
                        mn = np.nan

                if qilist:
                    if any(mmean['quality'].isin(qilist) is False):
                        me = np.nan
                    if any(mmin['quality'].isin(qilist) is False):
                        mx = np.nan
                    if any(mmax['quality'].isin(qilist) is False):
                        mn = np.nan

                self.cy_monthly_stats["mean"][m] = float("%.2f" % me)
                self.cy_monthly_stats["max"][m] = (
                    float("%.2f" % mx),
                    ", ".join([str(i) for i in mmax[mmax['data'] == mx].index.day])
                )
                self.cy_monthly_stats["min"][m] = (
                    float("%.2f" % mn),
                    ", ".join([str(i) for i in mmin[mmin['data'] == mn].index.day])
                )

            except KeyError:
                #print("Caught KeyError: {}".format(exc))
                self.cy_monthly_stats["mean"][m] = np.nan
                self.cy_monthly_stats["max"][m] = (np.nan, "")
                self.cy_monthly_stats["min"][m] = np.nan
            except:
                print("Caught KeyError GENERIC")
                raise

    def set_cy_yearly_stats(self, oatmean, year, perc=None, qilist=[]):
        """ set current year yearly stats

            Args:
                oat (obj): oat sensor object
                year (int): year to calculate statistics
                perc (int): if defined percentage of data availability
                            requested to calculate month statistics
                qilist (list): list of acceptable qualityIndex
                            values to calculate stistics
        """

        self.__init_cy_yearly_stats__()
        year = str(year)

        me = float("%.2f" % oatmean.ts[year]['data'].mean())
        msp = me * 100 / float(self.surface)

        if perc:
            #number of non null observations
            obsnum = oatmean.ts[year]['data'].count()
            if (obsnum / (365 + (1 * isleap(int(year))))) * 100 < perc:
                me = np.nan
                msp = np.nan
        if qilist:
            if any(oatmean.ts[year]['quality'].isin(qilist) is False):
                me = np.nan
                msp = np.nan

        self.cy_yearly_stats["mean"] = me
        self.cy_yearly_stats["specific_flow"] = msp

    def set_monthly_stats(self, oatmean, perc=None, qilist=[], good_months_perc=70):
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

    def set_yearly_stats(self, oatmean, perc=None, qilist=[], good_months_perc=70):
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
        self.__init_yearly_stats__()

    def set_duration_stats(self, oatmean, plot=True):
        """ set duration values for table and plot

        """
        self.__init_duration_stats()
        toat = oatmean.copy()

        # filter dataframe to only include dates of interest
        data = toat.ts[
            (toat.ts.index.to_datetime() > pd.datetime(begyear, 1, 1))
            &
            (toat.ts.index.to_datetime() < pd.datetime(endyear, 1, 1))]

        # remove na values from dataframe
        data = data.dropna()

        # take average of each day of year (from 1 to 366) over the selected period of record
        data['doy'] = data.index.dayofyear
        dailyavg = data[site].groupby(data['doy']).mean()

        data = np.sort(dailyavg)

        ## uncomment the following to use normalized discharge instead of discharge
        #mean = np.mean(data)
        #std = np.std(data)
        #data = [(data[i]-np.mean(data))/np.std(data) for i in range(len(data))]
        data = [(data[i]) / normalizer for i in range(len(data))]

        # ranks data from smallest to largest
        ranks = sp.rankdata(data, method='average')

        # reverses rank order
        ranks = ranks[::-1]

        # calculate probability of each rank
        prob = [(ranks[i]/(len(data)+1)) for i in range(len(data)) ]

        # plot data via matplotlib
        plt.plot(prob,data,label=site+' '+str(begyear)+'-'+str(endyear))


----------
        data = np.sort(toat.ts)
        ranks = sp.rankdata(data, method='average')
        ranks = ranks[::-1]
        prob = [100*(ranks[i]/(len(data)+1)) for i in range(len(data)) ]




    #TODO: implement correct historical statistics

    #def set_monthly_stats(self, oatmean, perc=None, qilist=[], good_months_perc=70):
        #""" set historic monthly stats

            #Args:
                #oat (obj): oat sensor object
                #perc (int): if defined percentage of data availability
                        #requested to calculate statistics
                #qilist (list): list of acceptable qualityIndex values
                        #to calculate stistics
                #good_months_perc: percentage of good months
                        #to calculate statistics
        #"""

        #self.__init_monthly_stats__()
        #toat = oatmean.copy()
        #toat.ts['year'] = toat.ts.index.year
        #toat.ts['month'] = toat.ts.index.month

        ##assign statistic period
        #try:
            #self.monthly_stats["from"] = dt.datetime.strptime(toat.data_availability[0], "%Y-%m-%dT%H:%M:%S.%fZ").year
            #self.monthly_stats["to"] = dt.datetime.strptime(toat.data_availability[1], "%Y-%m-%dT%H:%M:%S.%fZ").year
        #except ValueError:
            #self.monthly_stats["from"] = dt.datetime.strptime(toat.data_availability[0], "%Y-%m-%dT%H:%M:%S").year
            #self.monthly_stats["to"] = dt.datetime.strptime(toat.data_availability[1], "%Y-%m-%dT%H:%M:%S").year

        ##flow monthly statistics
        #for m in range(12):

            ##the month m in all the years
            #amm = toat.ts[toat.ts['month'] == m + 1]

            ##select years with sufficient data quality (n. of qilist data >perc)
            #yearlist = []
            #for y in toat.ts['year'].unique():

                #num = amm[
                        #(amm['month'] == m+1)
                        #& (amm['year'] == y)
                        #& (amm['quality'].isin(qilist))
                    #].count()['data']
                #den = amm[
                        #(amm['month'] == m+1)
                        #& (amm['year'] == y)
                    #].count()['data']
                #a = num / den
                #if a > perc/100:
                    #yearlist.append(y)

            ##====================
            ## data in yearlist

            ##if we have enough good months we calculate statistics
            #if (len(yearlist) / len(toat.ts['year'].unique())) > (good_months_perc/100):

                #mm = amm[amm['year'].isin(yearlist)]
                #grouper = mm.groupby('year').mean()

                ##monthly mean
                #self.monthly_stats["mean"][m] = float("%.2f" % grouper['data'].mean())

                ##max monthly average flow at colmo
                #maxc = float("%.2f" % grouper['data'].max())
                #self.monthly_stats["max_col"][m] = (
                    #float("%.2f" % maxc),
                    #", ".join([str(i) for i in grouper[grouper['data'] == maxc].index.values])
                    #)

                ##min monthly average flow at punta
                #minp = float("%.2f" % grouper['data'].min())
                #self.monthly_stats["min_pun"][m] = (
                    #float("%.2f" % minp),
                    #", ".join([str(i) for i in grouper[grouper['data'] == minp].index.values])
                    #)

                ##min





            #"max_col": [(np.nan, "") for x in range(12)],
            #"min_pun": [(np.nan, "") for x in range(12)],
            #"min_mean"