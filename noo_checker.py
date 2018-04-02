#!/usr/bin/python

# Written by Artem Findir
# The script is used to analyze FIXation logs in order to find Net Open Orders

'''script usage: ./noo_checker.py <path_to_risk_logger>'''

from __future__ import print_function
import re
import os.path
import sys
from collections import Counter
#import time

def show_help():
    print("\nScript usage: %s <path to risk logger file(s)>\n" % sys.argv[0])

if len(sys.argv[1:]) == 0: show_help()

def initial():
    '''Performs initial setup'''
    if not os.path.exists(logfile):
        sys.stderr.write("wrong path to the risk_log\n")
        sys.exit(3)

    global oids_per_ccy
    global total
    global total_rate
    global total_per_id
    global total_rate_per_id
    global oid_list
    global oid_check

    oids_per_ccy = dict()
    total = dict() #totals per ccy
    total_rate = dict() #totals x rate per ccy
    total_per_id = dict() #totals per oid
    total_rate_per_id = dict() #totals x rate per oid
    oid_list = []
    oid_check = []

def get_totals():
    '''Collect data'''
    global ccy_set #unique ccy pairs
    for line in open(logfile):
        match = re.match(r'.*;update\sopen;.*(?P<pos>(?<=POSITION=)[^,]*).*(?P<ccy>(?<=INS=)[^,]*).*(?P<side>(?<=SIDE=)-?\d).*(?P<rate>(?<=CONV_RATE=)\d+).*(?P<oid>(?<=OID=).{22})', line)
        if match != None:
            ccy = match.group("ccy")
            oid = match.group("oid")
            if not ccy in oids_per_ccy: oids_per_ccy[ccy] = []
            oids_per_ccy[ccy].append(oid)
            if not ccy in total: total[ccy] = 0
            total[ccy] += abs(int(match.group("pos"))) * int(match.group("side"))
            if not ccy in total_rate: total_rate[ccy] = 0
            total_rate[ccy] += abs(int(match.group("pos"))) * int(match.group("side")) * int(match.group("rate"))  # removed /10000
            if not oid in total_per_id: total_per_id[oid] = 0
            total_per_id[oid] += abs(int(match.group("pos"))) * int(match.group("side"))
            if not oid in total_rate_per_id: total_rate_per_id[oid] = 0
            total_rate_per_id[oid] += abs(int(match.group("pos"))) * int(match.group("side")) * int(match.group("rate"))
    ccy_set = total.keys()

def get_oid_list():
    '''Get IDs of open orders'''
    global oid_list
    for ccy in list(ccy_set):
        if total[ccy] != 0:
            oid_list += oids_per_ccy[ccy]
        if total[ccy] == 0 and total_rate[ccy] != 0:
            print("Stuck base detected")
            stuck_base(ccy)

def stuck_base(ccy):
    '''This function is being run only when NOO with "Stuck Base" is detected'''
    for oid in set(oids_per_ccy[ccy]):
        if total_rate_per_id[oid] != 0:
            discrepancy = total_rate_per_id[oid] / 10000
            print('Discrepancy: {:,d}\nCCY pair: {}\nOrder ID: {}\n-----'.format(discrepancy, ccy, oid))

def final():
    '''Output results for open orders'''
    for oid in total_per_id.keys():
        if total_per_id[oid] != 0: oid_check.append(oid)
    reduced_log = []
    for line in open(logfile):
        for id in oid_check:
            match = re.search(id, line)
            if match != None:
                reduced_log.append(line)
    for item in reduced_log:
        match = re.match(r'.*;update\sopen;.*(?P<pos>(?<=POSITION=)[^,]*).*(?P<ccy>(?<=INS=)[^,]*).*(?P<lp>(?<=LP=)[^,]*).*(?P<side>(?<=SIDE=)-?\d).*(?P<oid>(?<=OID=).*)', item)
        if match != None:
            print('\nAmount: {:,d}\nCCY pair: {}\nOrder ID: {}\nLP: {}\n-----'.format(abs(int(match.group("pos"))), match.group("ccy"), match.group("oid"), match.group("lp")))

if __name__ == "__main__":
#    start_time = time.time()
    for arg in sys.argv[1:]:
        logfile = arg
        print('\n*****%s*****' % (arg))
        initial()
        get_totals()
        get_oid_list()
        final()
#    elapsed_time = time.time() - start_time
#    print(elapsed_time)
