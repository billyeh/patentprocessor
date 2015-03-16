#!/usr/bin/env python

import uuid
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
- pat-type?
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

class Patent(PatentHandler):
    def __init__(self, root):
        self.root = root.xpath('/us-patent-grant')[0]
        xpaths = {
            'us_relation_list': '/us-patent-grant/us-bibliographic-data-grant/us-related-documents',
            'us_classifications': '/us-patent-grant/us-bibliographic-data-grant/classification-national',
            'ipcr_classifications': '/us-patent-grant/us-bibliographic-data-grant/classifications-ipcr/classification-ipcr',
        }
        self.country = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/country')
        self.patent = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/doc-number')
        self.kind = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/kind')
        self.date_grant = findtext(root, 'us-bibliographic-data-grant/publication-reference/document-id/date')
        self.pat_type = root.xpath('us-bibliographic-data-grant/application-reference')[0].get('appl-type')
        self.date_app = findtext(root, 'us-bibliographic-data-grant/application-reference/document-id/date')
        self.country_app = findtext(root, 'us-bibliographic-data-grant/application-reference/document-id/country')
        self.patent_app = findtext(root, 'us-bibliographic-data-grant/application-reference/document-id/doc-number')
        self.code_app = findtext(root, 'us-bibliographic-data-grant/us-application-series-code')
        self.clm_num = findtext(root, 'us-bibliographic-data-grant/number-of-claims')
        self.abstract = ''.join([stringify_children(el) for el in root.findall('abstract/p')])
        self.invention_title = ''.join([stringify_children(el) for el in root.findall('us-bibliographic-data-grant/invention-title')])
        print(self.__dict__)
        print(self.assignee_list)
        print(self.claims)
        print(self.citation_list)
        print(self.inventor_list)
        print(self.lawyer_list)

    def extract_location(self, addr):
        loc = {}
        loc['city'] = findtext(addr, 'address/city')
        loc['state'] = findtext(addr, 'address/state')
        loc['country'] = findtext(addr, 'address/country')
        loc['id'] = (u"|".join([loc['city'], loc['state'], loc['country']]).lower())
        return loc

    def extract_info(self, addr):
        asg = {}
        asg['name_first'] = findtext(addr, 'first-name')
        asg['name_last'] = findtext(addr, 'last-name')
        asg['organization'] = findtext(addr, 'orgname')
        asg['type'] = findtext(addr, 'role')
        asg['nationality'] = findtext(addr, 'address/country')
        asg['residence'] = findtext(addr, 'address/country')
        return asg

    @property
    def assignee_list(self):
        assignees = []
        for i, assignee in enumerate(self.root.findall('us-bibliographic-data-grant/assignees/assignee')):
            asg = assignee.find('addressbook')
            a, l = (self.extract_info(asg), self.extract_location(asg))
            a['sequence'] = i
            a['uuid'] = str(uuid.uuid1())
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
                data['kind'] = findtext(citation, './/kind')
                data['category'] = findtext(citation, './/category')
                data['date'] = findtext(citation, './/date')
                data['country'] = findtext(citation, './/country')
                data['number'] = findtext(citation, './/doc-number')
                data['sequence'] = ccnt
                data['uuid'] = str(uuid.uuid1())
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
            inv['uuid'] = str(uuid.uuid1())
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
            l['uuid'] = str(uuid.uuid1())
            lawyers.append(l)
        return lawyers

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

def parse_file(filename):
    num_docs = 0
    endtag_regex = re.compile('^<!DOCTYPE (.*) SYSTEM')
    endtag = ''
    with open(filename, 'r') as f:
        doc = []
        for line in f:
            doc.append(line)
            endtag = endtag_regex.findall(line) if not endtag else endtag
            if not endtag:
                continue
            terminate = re.compile('^</{0}>'.format(endtag[0]))
            if terminate.findall(line):
                num_docs += 1
                parse_document(''.join(doc))
                endtag = ''
                doc = []

def parse_document(docstring):
    if 'us-patent-grant' not in docstring: # one of those weird docs
        return
    doc = Patent(etree.fromstring(docstring))

if __name__ == '__main__':
    parse_file("ipg140415_short.xml")
