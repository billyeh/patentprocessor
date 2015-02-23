from lxml import etree

def parse_doc(doc_name):
    cur_doc = []
    with open(doc_name) as patent_file:
        for l in patent_file:
            if l == '<?xml version="1.0" encoding="UTF-8"?>':
                parse_file(cur_doc.join('\n'))
                cur_doc = []
            cur_doc.append(l)

def parse_file(s):
    tree = etree.parse(s)
    

if __name__ == '__main__':
    parse_doc("ipg140415.xml")
