from lxml import etree

v45_xpaths = {
    'country': '/us-patent-grant/us-bibliographic-data-grant/publication-reference/document-id/country',
    'patent': '/us-patent-grant/us-bibliographic-data-grant/publication-reference/document-id/doc-number',
    'kind': '/us-patent-grant/us-bibliographic-data-grant/publication-reference/document-id/kind',
    'date_grant': '/us-patent-grant/us-bibliographic-data-grant/publication-reference/document-id/date',
    'pat_type': '/us-patent-grant/us-bibliographic-data-grant/application-reference',
    'date_app': '/us-patent-grant/us-bibliographic-data-grant/application-reference/document-id/date',
    'country_app': '/us-patent-grant/us-bibliographic-data-grant/application-reference/document-id/country',
    'patent_app': '/us-patent-grant/us-bibliographic-data-grant/application-reference/document-id/doc-number',
    'code_app': '/us-patent-grant/us-bibliographic-data-grant/us-application-series-code',
    'clm_num': '/us-patent-grant/us-bibliographic-data-grant/number-of-claims',
    'abstract': '/us-patent-grant/abstract/p',
    'invention_title': '/us-patent-grant/us-bibliographic-data-grant/invention-title',
    'assignee_list': '/us-patent-grant/us-bibliographic-data-grant/assignees/assignee',
    'citation_list': '/us-patent-grant/us-bibliographic-data-grant/us-references-cited/us-citation',
    'inventor_list': '/us-patent-grant/us-bibliographic-data-grant/us-parties/inventors/inventor',
    'lawyer_list': '/us-patent-grant/us-bibliographic-data-grant/us-parties/agents/agent',
    'us_relation_list': '/us-patent-grant/us-bibliographic-data-grant/us-related-documents',
    'us_classifications': '/us-patent-grant/us-bibliographic-data-grant/classification-national',
    'ipcr_classifications': '/us-patent-grant/us-bibliographic-data-grant/classifications-ipcr/classification-ipcr',
    'claims': '/us-patent-grant/claims/claim'
}

def parse_file(file_name):
    parser = etree.XMLParser()
    with open(file_name) as patent_file:
        for l in patent_file:
            if l == '<?xml version="1.0" encoding="UTF-8"?>':
                parse_document(parser.close())
            parser.feed(l)
        parse_document(parser.close()) #parse the last file

def parse_document(root):
    print(etree.tostring(root))

if __name__ == '__main__':
    parse_document("ipg140415_short.xml")
