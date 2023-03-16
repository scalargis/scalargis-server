from xml.parsers import expat

class XmlParser(object):
    '''class used to retrive xml documents encoding
    '''

    def parse(self, xml):
        self.__parse(xml)

    def get_encoding(self):
        return self.encoding

    def get_version(self):
        return self.version

    def get_standalone(self):
        return self.standalone

    def __xml_decl_handler(self, version, encoding, standalone):
        self.encoding = encoding
        self.version = version
        self.standalone = standalone

    def __parse(self, xml):
        parser = expat.ParserCreate()
        parser.XmlDeclHandler = self.__xml_decl_handler
        parser.Parse(xml)