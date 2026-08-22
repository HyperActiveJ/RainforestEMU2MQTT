# This file originates in the Emu-Serial-API project by Rainforest Automation, Inc.
# (https://github.com/rainforestautomation/Emu-Serial-API). That project publishes NO
# licence -- it has no LICENSE file and states no terms -- so no reuse rights are granted
# by its authors, and none are granted here. It is included with this project for
# convenience, with attribution and no claim of ownership. See the NOTICE file at the root
# of this repository. The repository's LICENSE (MIT) covers this project's own code and
# does NOT cover this file.
#
# It is used here unmodified apart from this header.

from lxml import etree
from lxml import objectify



class MessageCluster():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return  self.xml_tree
        
        
class TimeCluster():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
    
class InstantaneousDemand():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    
class NetworkInfo():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        self.xml_tree = xml_tree
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
    
class PriceCluster():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
    
class DeviceInfo():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
    
class CurrentSummationDelivered():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
    
class ScheduleInfo():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
    
class BlockPriceDetail():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string

class ConnectionStatus():
    def __init__(self, xml_tree,block_string):
        self.block_string = block_string
        for element in xml_tree.iterchildren():
            setattr(self, element.tag, element.text)
    def __repr__(self):
        return self.block_string
        