#!/usr/bin/env python

import uuid
from datetime import datetime
import unicodedata
import lxml
import re

"""
Things to normalize:
- dates
- names
- remove empty strings and dictionaries 
    {k: v for k, v in asg.items()}
    if any(asg.values()) or any(loc.values()) minus uuid and sequence
- doc-number
- remove unnecessary fields, like nationality?
"""

from lxml import etree
from lib.handlers.handler import PatentHandler

def stringify_children(node):
    from lxml.etree import tostring
    s = [node.text]
    for c in node.getchildren():
        s.append(c.text)
        s.append(c.tail)
    return ''.join(filter(None, s))

def findtext(elem, path):
    return elem.findtext(path, default="")

def log(err):
    print(err)

def validate_patent(patent):

    def validate_date(date):
        if not re.search('^\d{6}', date):
            log('error in date: {0}'.format(date))
    def validate_country(country):
        if not re.search('^[A-Z]{2}$', country):
            log('error in country: {0}'.format(country))
    def validate_docnum(num):
        if not re.search('^[A-Z]{0,2}\d{6,8}$', num):
            log('error in patent: {0}'.format(num))
    def validate_kind(kind):
        if not re.search('^[A-Z]\d$', kind):
            log('error in kind: {0}'.format(kind))
    def validate_type(t):
        if not t in ('design utility reissue defensive publication statutory invention registration plant'):
            log('error in type: {0}'.format(t))
    def validate_code_app(ca):
        if not re.search('^\d{1,2}$', ca):
            log('error in code app: {0}'.format(ca))
    def validate_clm_num(c):
        if not re.search('^\d*$', c):
            log('error in code app: {0}'.format(c))
    def validate_asg_type(t):
        if not re.search('^0\d$', t):
            log('error in code app: {0}'.format(t))
    def validate_info(info):
        validate_country(info['nationality'])
        validate_asg_type(info['type'])
    def validate_location(loc):
        return
    def validate_assignees(assignees):
        for asg, loc in assignees:
            validate_info(asg)
            validate_location(loc)

    validate_country(patent.country)
    validate_docnum(patent.patent)
    validate_kind(patent.kind)
    validate_date(patent.date_grant)
    validate_type(patent.pat_type)
    validate_date(patent.date_app)
    validate_country(patent.country_app)
    validate_docnum(patent.patent_app)
    validate_code_app(patent.code_app)
    validate_clm_num(patent.clm_num)
    validate_assignees(patent.assignee_list)

class Patent(PatentHandler):
    def __init__(self, docstring, as_string=True):
        root = etree.fromstring(docstring)
        self.attributes = ['pat','app','assignee_list','patent','inventor_list','lawyer_list',
                     'us_relation_list','us_classifications','ipcr_classifications',
                     'citation_list','claims']
        try:
            self.root = root.xpath('/us-patent-grant')[0]
        except:
            pass
        self.country = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/country')
        self.patent = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/doc-number').lstrip('0')
        self.kind = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/kind')
        self.date_grant = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/date')
        self.pat_type = root.xpath('us-bibliographic-data-grant/application-reference')[0].get('appl-type')
        self.date_app = findtext(root, 'us-bibliographic-data-grant/application-reference/document-id/date')
        self.country_app = findtext(root, 'us-bibliographic-data-grant/application-reference/document-id/country')
        self.patent_app = findtext(root, 'us-bibliographic-data-grant/application-reference/document-id/doc-number').lstrip('0')
        self.code_app = findtext(root, 'us-bibliographic-data-grant/us-application-series-code')
        self.clm_num = findtext(root, 'us-bibliographic-data-grant/number-of-claims')
        self.abstract = ''.join([stringify_children(el) for el in root.findall('abstract/p')])
        self.invention_title = ''.join([stringify_children(el) for el in root.findall('us-bibliographic-data-grant/invention-title')])
        
        self.pat = {
            "id": self.patent,
            "type": self.pat_type,
            "number": self.patent,
            "country": self.country,
            "date": self.fix_date(self.date_grant),
            "abstract": self.abstract,
            "title": self.invention_title,
            "kind": self.kind,
            "num_claims": self.clm_num
        }
        self.app = {
            "type": self.code_app,
            "number": self.patent_app,
            "country": self.country_app,
            "date": self.fix_date(self.date_app),
            "id": str(self.date_app)[:4] + "/" + self.patent_app
        }

    def fix_date(self, datestring):
        if not datestring:
            return None
        elif datestring[:4] < "1900":
            return None
        # default to first of month in absence of day
        if datestring[-4:-2] == '00':
            datestring = datestring[:-4] + '01' + datestring[-2:]
        if datestring[-2:] == '00':
            datestring = datestring[:6] + '01'
        try:
            datestring = datetime.strptime(datestring, '%Y%m%d')
            return datestring
        except Exception as inst:
            print inst, datestring
            return None

    def extract_location(self, addr):
        loc = {}
        loc['city'] = findtext(addr, './/city')
        loc['state'] = findtext(addr, './/state')
        loc['country'] = findtext(addr, './/country')
        loc['id'] = (u"|".join([loc['city'], loc['state'], loc['country']]).lower())
        return loc

    def extract_info(self, addr):
        asg = {}
        asg['name_first'] = findtext(addr, './/first-name')
        asg['name_last'] = findtext(addr, './/last-name')
        asg['organization'] = findtext(addr, './/orgname')
        asg['type'] = findtext(addr, './/role')
        asg['nationality'] = findtext(addr, './/address/country')
        asg['residence'] = findtext(addr, './/address/country')
        asg['uuid'] = str(uuid.uuid1())
        return asg

    def extract_doc(self, doc):
        d = {}
        d['country'] = findtext(doc, './/country')
        d['kind'] = findtext(doc, './/kind')
        d['date'] = self.fix_date(findtext(doc, './/date'))
        d['number'] = findtext(doc, './/doc-number').lstrip('0')
        d['category'] = findtext(doc, './/category')
        d['uuid'] = str(uuid.uuid1())
        return d

    def extract_class(self, cl):
        c = {}
        text = cl.text
        c['class'] = text[:3].replace(' ', '')
        c['subclass'] = text[3:].replace(' ', '')
        return [{'uuid': str(uuid.uuid1())},
                {'id': c['class'].upper()},
                {'id': "{class}/{subclass}".format(**c).upper()}]

    @property
    def assignee_list(self):
        assignees = []
        for i, assignee in enumerate(self.root.findall('us-bibliographic-data-grant/assignees/assignee')):
            a, l = (self.extract_info(assignee), self.extract_location(assignee))
            a['sequence'] = i
            assignees.append([a, l])
        return assignees

    @property
    def citation_list(self):
        regular_cits = []
        other_cits = []
        ocnt = 0
        ccnt = 0
        for citation in self.root.findall('us-bibliographic-data-grant/us-references-cited/us-citation'):
            data = {}
            othercit = findtext(citation, './/othercit')
            if othercit:
                data['text'] = othercit
                data['sequence'] = ocnt
                data['uuid'] = str(uuid.uuid1())
                other_cits.append(data)
                ocnt += 1
            else:
                data = self.extract_doc(citation)
                data['sequence'] = ccnt
                regular_cits.append(data)
                ccnt += 1
        return [regular_cits, other_cits]

    @property
    def inventor_list(self):
        inventors = []
        for i, inventor in enumerate(self.root.findall('us-bibliographic-data-grant/us-parties/inventors/inventor')):
            inve = inventor.find('addressbook')
            inv, loc = (self.extract_info(inve), self.extract_location(inve))
            inv['sequence'] = i
            inventors.append([inv, loc])
        return inventors

    @property
    def lawyer_list(self):
        lawyers = []
        for i, lawyer in enumerate(self.root.findall('us-bibliographic-data-grant/us-parties/agents/agent')):
            law = lawyer.find('addressbook')
            l = self.extract_info(law)
            l['country'] = findtext(law, './/country')
            l['sequence'] = i
            l['organization_upper'] = l['organization'].upper()
            lawyers.append(l)
        return lawyers

    @property
    def us_relation_list(self):
        relations = []
        i = 0
        for reldoc in self.root.findall('us-bibliographic-data-grant/us-related-documents'):
            if reldoc.tag not in ['related-publication', 'us-provisional-application']:
                pass
            data = self.extract_doc(reldoc)
            data['doctype'] = reldoc.tag
            data['sequence'] = i
            i += 1
            relations.append(data)
            for relation in reldoc.findall('.//relation'):
                for relationship in ['parent-doc', 'parent-grant-document', 'parent-pct-document', 'child-doc']:
                    rel = relation.findall(relationship)
                    for r in rel:
                        data = self.extract_doc(r)
                        data['doctype'] = r.tag
                        data['relationship'] = r.tag
                        data['status'] = findtext(r, 'parent-status')
                        data['sequence'] = i
                        i += 1
                        relations.append(data)
        return relations

    @property
    def us_classifications(self):
        classes = []
        i = 0
        classifications = [self.root.find('us-bibliographic-data-grant/classification-national/main-classification')] + \
                self.root.findall('us-bibliographic-data-grant/classification-national/further-classification')
        for classification in classifications:
            c = self.extract_class(classification)
            c[0]['sequence'] = i
            i += 1
            classes.append(c)
        return classes

    @property
    def ipcr_classifications(self):
        ipcrs = []
        for i, ipcr in enumerate(self.root.findall('us-bibliographic-data-grant/classifications-ipcr/classification-ipcr')):
            data = {}
            for tag in ['classification-level', 'section',
                        'class', 'subclass', 'main-group', 'subgroup', 'symbol-position',
                        'classification-value', 'classification-status',
                        'classification-data-source']:
                data[tag] = findtext(ipcr, tag)
            data['ipc_version_indicator'] = self.fix_date(findtext(ipcr, 'ipc-version-indicator/date'))
            data['action_date'] = self.fix_date(findtext(ipcr, 'action-date/date'))
            data['sequence'] = i
            data['uuid'] = str(uuid.uuid1())
            ipcrs.append(data)
        return ipcrs

    @property
    def claims(self):
        claims = []
        for i, claim in enumerate(self.root.findall('claims/claim/claim-text')):
            data = {}
            data['text'] = re.compile(r'^\d+\. *').sub('', stringify_children(claim))
            data['uuid'] = str(uuid.uuid1())
            data['sequence'] = i+1 # claims are 1-indexed
            ref = findtext(claim, 'claim-ref')
            if ref:
                data['dependent'] = int(ref.split(' ')[-1])
            claims.append(data)
        return claims
