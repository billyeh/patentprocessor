#!/usr/bin/env python

import pymongo
import pandas as pd
import datetime

from pymongo import MongoClient
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from scipy.stats import mode
from unidecode import unidecode
from lib.alchemy.schema import GrantBase, ApplicationBase
from lib.alchemy import session_generator

GRANT = 'grant'
APP = 'app'
TOLERANCE = .1 # how many std's the new mean is allowed to deviate from the latest

"""
client = MongoClient()

db = client.stat_database
"""

grant_stat = {}
app_stat = {}

"""
grant_stats = db.grant_stats
app_stats = db.app_stats
"""

sessiongen = session_generator(dbtype='grant')
session = sessiongen()

def printstats(series, name, db):
    print name
    stat = {'mean': series.mean(), 'median': series.median(), 'mode': mode(series)[0][0],
            'std': series.std(), 'min': series.min(), 'max': series.max()}
    for s in ['mean', 'median', 'mode', 'std', 'min', 'max']:
        print s, stat[s]
    if db == GRANT:
        grant_stat[name] = stat
    else:
        app_stat[name] = stat

counts =[]
tablekeys = []
tables = GrantBase.metadata.tables
rawtables = tables.keys()
for table in rawtables:
    res = session.execute('select count(*) from {0}'.format(table)).fetchone()[0]
    if res:
        counts.append(res)
        tablekeys.append(table)
d = pd.DataFrame.from_dict({'tables': tablekeys, 'count': map(lambda x: int(x), counts)})
d.index = d['tables']

patent_count = session.execute('select count(*) from patent;').fetchone()[0]
app_count = session.execute('select count(*) from application;').fetchone()[0]

rawinventor_count = session.execute('select count(*) from rawinventor;').fetchone()[0]
disambiginventor_count = session.execute('select count(*) from inventor;').fetchone()[0]

rawassignee_count = session.execute('select count(*) from rawassignee;').fetchone()[0]
disambigassignee_count = session.execute('select count(*) from assignee;').fetchone()[0]

rawlawyer_count = session.execute('select count(*) from rawlawyer;').fetchone()[0]
disambiglawyer_count = session.execute('select count(*) from lawyer;').fetchone()[0]

rawlocation_count = session.execute('select count(*) from rawlocation;').fetchone()[0]
disambiglocation_count = session.execute('select count(*) from location;').fetchone()[0]

d = pd.DataFrame.from_dict({'raw': [patent_count,'',rawinventor_count,rawassignee_count,rawlawyer_count,rawlocation_count],
                           'disambig': ['', app_count, disambiginventor_count, disambigassignee_count, disambiglawyer_count, disambiglocation_count],
                           'labels': ['patent','application','inventor','assignee','lawyer','location']})
print(d[['labels','raw','disambig']])

res = session.execute('select count(*) from rawinventor group by patent_id;')
inventor_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': inventor_counts})
printstats(d['count'], 'inventors/patent', GRANT)
print 'Total:', session.execute('select count(*) from rawinventor;').fetchone()[0]

session = sessiongen()
res = session.execute('select count(*) from patent_inventor group by inventor_id;')
patent_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': patent_counts})
printstats(d['count'], 'patents/inventor', GRANT)
print 'Total:', session.execute('select count(*) from rawinventor;').fetchone()[0]

res = session.execute('select location.state, count(*) from rawinventor \
                       left join rawlocation on rawinventor.rawlocation_id = rawlocation.id \
                       left join location on location.id = rawlocation.location_id \
                       where location.country = "US" and length(location.state) = 2 group by location.state ')
data = res.fetchall()
inventor_counts = [int(x[1]) for x in data]
inventor_states = [unidecode(x[0]) for x in data]
d = pd.DataFrame.from_dict({'count': inventor_counts, 'states': inventor_states})
d.index = d['states']
printstats(d['count'], 'inventors/state', GRANT)
print len(d['states'])

res = session.execute('select rawlocation.state, count(distinct rawlocation.city) from rawlocation \
                       where rawlocation.country = "US" and length(rawlocation.state) = 2 \
                       group by rawlocation.state')
data = res.fetchall()
d = pd.DataFrame.from_records(data)
d.columns = ['state','count']
d.index = d['state']
printstats(d['count'], 'cities/state', GRANT)
print sum(d['count'])

res = session.execute('select location.state, count(distinct location.city) from location \
                       where location.country = "US" and length(location.state) = 2 \
                       group by location.state')
data = res.fetchall()
d = pd.DataFrame.from_records(data)
d.columns = ['state','count']
d.index = d['state']
printstats(d['count'], 'disambiguated locations/state', GRANT)
print sum(d['count'])

res = session.execute("select location.state, count(*) from patent \
                       left join rawinventor on rawinventor.patent_id = patent.id \
                       left join rawlocation on rawlocation.id = rawinventor.rawlocation_id \
                       right join location on location.id = rawlocation.location_id \
                       where length(location.state) = 2 and rawinventor.sequence = 0 \
                       and location.country = 'US' \
                       group by location.state")
data = res.fetchall()
d = pd.DataFrame.from_records(data)
d.columns = ['state','count']
d.index = d['state']
printstats(d['count'], 'patents/state', GRANT)
print sum(d['count'])

res = session.execute('select year(date), count(*) from patent group by year(date);')
year_counts = map(lambda x: (str(int(x[0])), int(x[1])), res.fetchall())
d = pd.DataFrame.from_dict({'dates': [x[0] for x in year_counts], 'count': [x[1] for x in year_counts]})
d.index = d['dates']
printstats(d['count'], 'patents/year', GRANT)
print sum(d['count'])

res = session.execute('select year(application.date), count(*) from patent \
                       left join application on application.patent_id = patent.id \
                       where year(application.date) != "" \
                       group by year(application.date);')
year_counts = map(lambda x: (str(int(x[0])), int(x[1])), res.fetchall())
d = pd.DataFrame.from_dict({'dates': [x[0] for x in year_counts], 'count': [x[1] for x in year_counts]})
d.index = d['dates']
printstats(d['count'], 'applications/year', GRANT)
print sum(d['count'])

res = session.execute('select count(*) from rawassignee group by organization;')
data = res.fetchall()
d = pd.DataFrame.from_dict({'count': [int(x[0]) for x in data]})
printstats(d['count'], 'assignees/organization', GRANT)

res = session.execute('select count(*) from rawlawyer group by organization;')
data = res.fetchall()
d = pd.DataFrame.from_dict({'count': [int(x[0]) for x in data]})
printstats(d['count'], 'lawyers/organization', GRANT)

res = session.execute('select count(*) from uspatentcitation group by patent_id;')
cit_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': cit_counts})
printstats(d['count'], 'forward citations/patent', GRANT)
res = session.execute('select count(*) from uspatentcitation group by citation_id;')
cit_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': cit_counts})
printstats(d['count'], 'backward citations/patent', GRANT)

res = session.execute('select count(*) from foreigncitation group by patent_id;')
cit_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': cit_counts})
printstats(d['count'], 'forward foreign citations/patent', GRANT)
res = session.execute('select count(*) from foreigncitation group by number;')
cit_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': cit_counts})
printstats(d['count'], 'backward foreign citations/patent', GRANT)

res = session.execute('select count(*) from otherreference group by patent_id;')
cit_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': cit_counts})
printstats(d['count'], 'forward other citations/patent', GRANT)

res = session.execute('select count(*) from usapplicationcitation group by patent_id;')
cit_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': cit_counts})
printstats(d['count'], 'forward application citations/patent', GRANT)

sessiongen = session_generator(dbtype='application')
session = sessiongen()

counts =[]
tablekeys = []
tables = ApplicationBase.metadata.tables
rawtables = tables.keys()
for table in rawtables:
    res = session.execute('select count(*) from {0}'.format(table)).fetchone()[0]
    if res:
        counts.append(res)
        tablekeys.append(table)
d = pd.DataFrame.from_dict({'tables': tablekeys, 'count': map(lambda x: int(x), counts)})
d.index = d['tables']

patent_count = session.execute('select count(*) from application;').fetchone()[0]

rawinventor_count = session.execute('select count(*) from rawinventor;').fetchone()[0]
disambiginventor_count = session.execute('select count(*) from inventor;').fetchone()[0]

rawassignee_count = session.execute('select count(*) from rawassignee;').fetchone()[0]
disambigassignee_count = session.execute('select count(*) from assignee;').fetchone()[0]

rawlocation_count = session.execute('select count(*) from rawlocation;').fetchone()[0]
disambiglocation_count = session.execute('select count(*) from location;').fetchone()[0]

d = pd.DataFrame.from_dict({'raw': [patent_count,rawinventor_count,rawassignee_count,rawlocation_count],
                           'disambig': ['N/A',disambiginventor_count, disambigassignee_count, disambiglocation_count],
                           'labels': ['application','inventor','assignee','location']})
d[['labels','raw','disambig']]

res = session.execute('select count(*) from rawinventor group by application_id;')
inventor_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': inventor_counts})
printstats(d['count'], 'inventors/application', APP)
print 'Total:', session.execute('select count(*) from rawinventor;').fetchone()[0]

session = sessiongen()
res = session.execute('select count(*) from application_inventor group by inventor_id;')
patent_counts = [x[0] for x in res.fetchall()]
d = pd.DataFrame.from_dict({'count': patent_counts})
printstats(d['count'], 'applications/inventor', APP)
print 'Total:', session.execute('select count(*) from rawinventor;').fetchone()[0]

res = session.execute('select location.state, count(*) from rawinventor \
                       left join rawlocation on rawinventor.rawlocation_id = rawlocation.id \
                       left join location on location.id = rawlocation.location_id \
                       where location.country = "US" and length(location.state) = 2 group by location.state ')
data = res.fetchall()
inventor_counts = [int(x[1]) for x in data]
inventor_states = [unidecode(x[0]) for x in data]
d = pd.DataFrame.from_dict({'count': inventor_counts, 'states': inventor_states})
d.index = d['states']
printstats(d['count'], 'inventors/state', APP)
print len(d['states'])

res = session.execute('select rawlocation.state, count(distinct rawlocation.city) from rawlocation \
                       where rawlocation.country = "US" and length(rawlocation.state) = 2 \
                       group by rawlocation.state')
data = res.fetchall()
d = pd.DataFrame.from_records(data)
d.columns = ['state','count']
d.index = d['state']
printstats(d['count'], 'locations/state', APP)
print sum(d['count'])

res = session.execute('select location.state, count(distinct location.city) from location \
                       where location.country = "US" and length(location.state) = 2 \
                       group by location.state')
data = res.fetchall()
d = pd.DataFrame.from_records(data)
d.columns = ['state','count']
d.index = d['state']
printstats(d['count'], 'disambiguated locations/state', APP)
print sum(d['count'])

res = session.execute("select location.state, count(*) from application \
                       left join rawinventor on rawinventor.application_id = application.id \
                       left join rawlocation on rawlocation.id = rawinventor.rawlocation_id \
                       right join location on location.id = rawlocation.location_id \
                       where length(location.state) = 2 and rawinventor.sequence = 0 \
                       and location.country = 'US' \
                       group by location.state")
data = res.fetchall()
d = pd.DataFrame.from_records(data)
d.columns = ['state','count']
d.index = d['state']
printstats(d['count'], 'applications/state', APP)
print sum(d['count'])

res = session.execute('select year(date), count(*) from application group by year(date);')
year_counts = map(lambda x: (str(int(x[0])), int(x[1])), res.fetchall())
d = pd.DataFrame.from_dict({'dates': [x[0] for x in year_counts], 'count': [x[1] for x in year_counts]})
d.index = d['dates']
printstats(d['count'], 'applications/year', APP)
print sum(d['count'])

res = session.execute('select count(*) from rawassignee group by organization;')
data = res.fetchall()
d = pd.DataFrame.from_dict({'count': [int(x[0]) for x in data]})
printstats(d['count'], 'applications/assignee', APP)

latest_grant_stat = grant_stats.find().sort([['_id', -1]]).limit(1).next()
latest_app_stat = app_stats.find().sort([['_id', -1]]).limit(1).next()

grant_stats.insert(grant_stat)
app_stats.insert(app_stat)

def check_stat(new_stat, old_stat):
    for name, stat in new_stat.iteritems():
        if not type(stat) == dict or not 'mean' in new_stat or not 'mean'in old_stat:
            continue
        if new_stat['mean'] - old_stat['mean'] > TOLERANCE*old_stat['std']:
            print('Detected large deviation in ' + name)

if not latest_grant_stat:
    print('No prior grant stats found, comparison check not performed')
else:
    check_stat(grant_stat, latest_grant_stat)
if not latest_app_stat:
    print('No prior app stats, found, comparison check not performed')
else:
    check_stat(app_stat, latest_app_stat)
