#!/usr/bin/env
# written by Danny Wagstaff 9/2017

from datetime import date, timedelta
import urllib3
import certifi
import json

class Basket(list):
    def __init__(self, name = '', val = list()):
        self.name = name
        self.value = val

    def getDlvDates(self, dt = date.today()):
        '''
        Returns first and last days of the delivery month (March, June, September, or December) for the US Treasury (UST) futures contract
        '''
        day1DelMth = dt
        if dt.month%3 == 0:     # Mar,Jun, Sep, Dec
            day1DelMth = date(dt.year, dt.month, 1)
        elif dt.month%3 == 1:   # Jan, Apr, Jul, Oct
            day1DelMth = date(dt.year, dt.month + 2, 1)
        else:                   # Feb, May, Aug, Nov
            day1DelMth = date(dt.year, dt.month + 1, 1)
        dayLastDelMth = date(day1DelMth.year, day1DelMth.month + 1, 1) - timedelta(days = 1)
        return (day1DelMth, dayLastDelMth)

    def getConAbbr(self, conPrefix = '', dt = date.today()):
        '''
        Returns a 4 character string: the UST futures contract abbreviation, which consists of the contract (TU, FV, TY, TN, US, OR UB), 
        the expiration month (H = March, M = June, U = September, Z = December), and the last digit of the expiration year
        '''
        dictFrontContract = {1: "H", 2: "H", 3: "H", 4: "M", 5: "M", 6: "M", 7: "U", 8: "U", 9: "U", 10: "Z", 11: "Z", 12: "Z"}
        return ''.join([conPrefix, dictFrontContract[dt.month], str(dt.year)[3]])

    def getMatDate(self, ustSec):
        '''
        Returns the maturity date of a UST security in yyyy-mm-dd form
        '''
        return date(int(ustSec["maturityDate"][0:4]), int(ustSec["maturityDate"][5:7]), int(ustSec["maturityDate"][8:10]))

    def getWebPg(self, sec = "Note"):
        '''
        Uses urllib3 to get and return a list of UST securities (either notes or bonds) from treasurydirect.gov's API
        '''
        urlObj = urllib3.PoolManager(cert_reqs = "CERT_REQUIRED", ca_certs = certifi.where())
        return urlObj.request("GET", ''.join(["https://www.treasurydirect.gov/TA_WS/securities/search?format=json&type=", sec]))

    def getSpecs(self, FC):
        '''
        Returns 1) the minimum time between the first day of the delivery month and the UST security's maturity date, and
                2) the maximum time between the last day of the delivery month and the UST security's maturity date
        The specifications for each UST futures contract are listed below for reference (copied from
        http://www.cmegroup.com/trading/interest-rates/#uSTreasuries)
        
        TU Contract Delivery Specifications
        U.S. Treasury notes with an original term to maturity of 
        1) not more than five years and three months and a remaining term to maturity of 
        2) not less than one year and nine months from the first day of the delivery month and a remaining 
        term to maturity of 
        3) not more than two years from the last day of the delivery month. 
        
        FV Contract Delivery Specifications
        U.S. Treasury notes with an original term to maturity of 
        1) not more than five years and three months and a remaining term to maturity of 
        2) not less than 4 years and two months as of the first day of the delivery month. 
        
        TY Contract Delivery Specifications
        U.S. Treasury notes with an remaining term to maturity of
        1) at least 6.5 years as of the first day of the delivery month.     
        2) not more than 10 years as of the first day of the delivery month. 
        
        TN Contract Delivery Specifications
        Original issue 10 Year U.S. Treasury notes with an remaining term to maturity of
        1) at least 9.41667 years (9 years, 5 months)  as of the first day of the delivery month.     
        2) not more than 10 years as of the first day of the delivery month. 
        
        US Contract Delivery Specifications
        U.S. Treasury notes with an remaining term to maturity of
        1) at least 15 years as of the first day of the delivery month.     
        2) not more than 25 years as of the first day of the delivery month. 
        
        UB Contract Delivery Specifications
        U.S. Treasury notes with an remaining term to maturity of
        1) at least 25 years as of the first day of the delivery month.     
        '''
        dictSpecs = {'TU': {'TTM_Min': 1.75, 'maxToDayLast': 2}, 'FV': {'TTM_Min': 4.1667, 'maxToDayLast': 5.25},'TY': {'TTM_Min': 6.5, 'maxToDayLast': 10.0833},
        'TN': {'TTM_Min': 9.4167, 'maxToDayLast': 10.0833}, 'US': {'TTM_Min': 15, 'maxToDayLast': 25.0833}, 'UB': {'TTM_Min': 25, 'maxToDayLast': 30.0833}}
        return dictSpecs[FC]
        
    
    def getTerms(self, FC):
        '''
        Returns a dictionary of original times to maturity of UST securities eligible to be delivered into the UST futures contract (given by FC)
        '''
        Terms={'TU': {"2-Year": 2, "3-Year": 3, "5-Year": 5}, 'FV': {"5-Year": 5}, 'TY': {"7-Year": 7, "9-Year 10-Month": 9.8333, "9-Year 11-Month": 9.9167, "10-Year": 10}, \
               'TN': {"9-Year 10-Month": 9.8333, "9-Year 11-Month": 9.9167, "10-Year": 10}, 'US': {"29-Year 10-Month": 29.8333, "29-Year 11-Month": 29.9167,"30-Year": 30}, \
               'UB': {"29-Year 10-Month": 29.8333, "29-Year 11-Month": 29.9167, "30-Year": 30}}
        return Terms[FC]


    def getBasket(self, FC = 'TU'):
        '''
        Goes through the list of UST securities gotten previously from the getWebPg method, and generates a list
        of securities eligible to be delivered into the UST futures contract (passed to the method as FC), which is stored in self.value
        '''
        self.value = [] # start with empty list
        if FC in ['US', 'UB']: # US=bond contract (>=15 yrs to maturity); UB=ultra bond (>=25 yrs to maturity)
            tsyDrct = self.getWebPg("Bond") # US Treasury securities deliverable into US or UB contracts
        else:
            tsyDrct = self.getWebPg("Note") # US Treasury securities deliverable into TU (2 yr), FV (5 yr), TY (original 10 yr), TN (ultra 10 yr) contracts
        (day1DelMth, dayLastDelMth) = self.getDlvDates()
        dictUSTSecs = json.loads(tsyDrct.data.decode("utf-8"))
        dictTerms = self.getTerms(FC)
        dictSpecs = self.getSpecs(FC)
        secCount = 0
        listCUSIP = []
        for TSec in dictUSTSecs:
            edgeCase = ''
            # check to see if bond's original term satisfies contract specs (mostly applies to TU contract)
            if TSec["term"] in dictTerms:
                USTMatDate = self.getMatDate(TSec)
                # check to see if conditions 1) and 2) are satisfied
                # dateutil is not available through A2 Hosting; must do something else to calculate dateDiff1 and dateDiff2
                #dateDiff1=relativedelta(USTMatDate,day1DelMth).years+relativedelta(USTMatDate,day1DelMth).months/12+relativedelta(USTMatDate,day1DelMth).days/365.25
                #dateDiff2=relativedelta(USTMatDate,dayLastDelMth).years+relativedelta(USTMatDate,dayLastDelMth).months/12+relativedelta(USTMatDate,dayLastDelMth).days/365.25
                dateDiff1 = (USTMatDate-day1DelMth).days / 365.25 # just an approximation!
                dateDiff2 = (USTMatDate - dayLastDelMth).days / 365.25 # just an approximation!
                # this may include/exclude a security on the "edge" of the basket
                if dateDiff1 >= dictSpecs["TTM_Min"] and dateDiff2 <= dictSpecs['maxToDayLast']:
                    # temporary marking of possible edge cases
                    if abs(dateDiff1 - dictSpecs["TTM_Min"]) <= 0.005:
                        edgeCase = '**'
                    # check to see if condition TU 3) is satisfied
                    if dateDiff2 <= max(dictTerms.values()):
                        for tenor in dictTerms:
                            if abs(dateDiff2 - dictTerms[tenor]) <= 0.005:
                                edgeCase = '**'
                        # must check for When Issued (WI) notes and reopenings, as these are not deliverable securities
                        # Also make sure we don't already have the security in our list
                        if len(TSec["interestRate"]) > 0 and not (TSec["cusip"] in listCUSIP): 
                            secCount = secCount + 1
                            TTM = (USTMatDate - date.today()).days / 365.25
                            TTM = str('%.2f' % TTM)
                            TSec['lowYield'] = '%.2f' % float(TSec['lowYield'])
                            self.value.append({'matDate': ''.join([TSec["maturityDate"][0:10], edgeCase]), 'intRate': float(TSec["interestRate"]), \
                                             'cpnsPerYr': 2, 'TTM': TTM, 'cusip': TSec["cusip"], 'issueDate': TSec['issueDate'][0:10], \
                                             'lowYield': TSec['lowYield']})
                            listCUSIP.append(TSec["cusip"])
