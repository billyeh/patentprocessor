#!/usr/bin/env python

from lxml import etree
from lib.handlers.handler import PatentHandler

class Patent(PatentHandler):

    def __init__(self, root):
        root = root.xpath('/us-patent-grant')[0]
        xpaths = {
            'assignee_list': '/us-patent-grant/us-bibliographic-data-grant/assignees/assignee',
            'citation_list': '/us-patent-grant/us-bibliographic-data-grant/us-references-cited/us-citation',
            'inventor_list': '/us-patent-grant/us-bibliographic-data-grant/us-parties/inventors/inventor',
            'lawyer_list': '/us-patent-grant/us-bibliographic-data-grant/us-parties/agents/agent',
            'us_relation_list': '/us-patent-grant/us-bibliographic-data-grant/us-related-documents',
            'us_classifications': '/us-patent-grant/us-bibliographic-data-grant/classification-national',
            'ipcr_classifications': '/us-patent-grant/us-bibliographic-data-grant/classifications-ipcr/classification-ipcr',
            'claims': '/us-patent-grant/claims/claim'
        }
        self.country = root.xpath('us-bibliographic-data-grant/publication-reference/document-id/country')[0].text
        self.patent = root.xpath('us-bibliographic-data-grant/publication-reference/document-id/doc-number')[0].text
        self.kind = root.xpath('us-bibliographic-data-grant/publication-reference/document-id/kind')[0].text
        self.date_grant = root.xpath('us-bibliographic-data-grant/publication-reference/document-id/date')[0].text
        self.pat_type = root.xpath('us-bibliographic-data-grant/application-reference')[0].get('appl-type')
        self.date_app = root.xpath('us-bibliographic-data-grant/application-reference/document-id/date')[0].text
        self.country_app = root.xpath('us-bibliographic-data-grant/application-reference/document-id/country')[0].text
        self.patent_app = root.xpath('us-bibliographic-data-grant/application-reference/document-id/doc-number')[0].text
        self.code_app = root.xpath('us-bibliographic-data-grant/us-application-series-code')[0].text
        self.clm_num = root.xpath('us-bibliographic-data-grant/number-of-claims')[0].text
        self.abstract = ''.join([el.text for el in root.xpath('abstract/p')])
        self.invention_title = ''.join([el.text for el in root.xpath('us-bibliographic-data-grant/invention-title')])

        print(self.__dict__)


def parse_file(file_name):
    parser = etree.XMLParser()
    with open(file_name) as patent_file:
        for l in patent_file:
            if l == '<?xml version="1.0" encoding="UTF-8"?>':
                parse_document(parser.close())
            parser.feed(l)
        parse_document(parser.close()) #parse the last file

def parse_document(root):
    doc = Patent(root)

if __name__ == '__main__':
    parse_file("ipg140415_short.xml")
