#!/usr/bin/env python 
from lxml import etree
from lxml import objectify
import api_classes
import argparse
from io import StringIO, BytesIO
import re,json,sys,os, subprocess,io,copy,threading,platform,time,serial

def recursive_dict(element):
     return element.tag, dict(list(map(recursive_dict, element))) or element.text
     
     
class emu():
    obj_type="emu_serial"
    #this is a list of all tags that are possible in the emu!
    #list of xml  root tags
    command_root= etree.Element('Command')
    command_firmware= etree.Element('Firmware')
    #list of tags that might be nested
    command_name= etree.Element('Name')
    #used in set meter attributes
    multiplier =etree.Element('Multiplier')
    divisor=etree.Element('Divisor')
    #used in set_fast_poll
    frequency=etree.Element('Frequency')
    duration = etree.Element('Duration')
    _type = etree.Element('Type')
    confirm = etree.Element('Confirm')
    refresh = etree.Element('Refresh')
    #used for set_current_price
    trailing_digits= etree.Element('TrailingDigits')
    currency= etree.Element('Currency')
    price= etree.Element('Price')
    #used for set_meter_info
    nickname= etree.Element('Nickname')
    account= etree.Element('Account')
    auth= etree.Element('Auth')
    host = etree.Element('Host')
    enabled = etree.Element('Enabled')
    #billing periods
    _id = etree.Element('Id')
    current_day_max_demand= etree.Element('CurrentDayMaxDemand')
    number_of_periods= etree.Element('NumberOfPeriods')
    period= etree.Element('Period')
    start = etree.Element('Start')
    current_day_maximum_demand= etree.Element('CurrentDayMaximumDemand')
    #price_blocks
    device_mac_id = etree.Element('DeviceMacId')
    meter_mac_id= etree.Element('MeterMacId')
    time_stamp= etree.Element('TimeStamp')
    number_of_blocks= etree.Element('NumberOfBlocks')
    threshold_1 = etree.Element('Threshold1')
    threshold_2 = etree.Element('Threshold2')
    threshold3= etree.Element('Threshold3')
    threshold4= etree.Element('Threshold4')
    threshold= etree.Element('Threshold')
    interval_channel = etree.Element('IntervalChannel')
    end_time = etree.Element('EndTime')
    event = etree.Element('Event')
    mode = etree.Element('Mode')
    offset = etree.Element('Offset')
    blk_size = etree.Element('BlkSize')
    version = etree.Element('Version')
    img_type = etree.Element('ImgType')
    mfg_code = etree.Element('MfgCode')
    erase = etree.Element('Erase')
    img_size = etree.Element('ImgSize')
    blk = etree.Element('Blk')
    blk_size = etree.Element('BlkSize')
    block = etree.Element('Block')
    crc_16= etree.Element('crc16')
    new_ver= etree.Element('NewVer')
    write_buffer=''
    block_string=""
    tag_block=False
    tag=""
    data = dict()
    state = dict()
    responseRoots = ['NetworkInfo','ApsTable','Information', 'TimeCluster','NwkTable','Information','PriceCluster','DeviceInfo','Google','SimpleMeteringCluster','InstantaneousDemand','BlockPriceDetail','ConnectionStatus','BillingPeriodList','MessageCluster','FastPollStatus','CurrentSummationDelivered','NetworkInfo']
    #command list (tag Name values)
    cmd_restart = "restart"
    cmd_get_restart_info ="get_restart_info"
    cmd_set_restart_info ="set_restart_info"
    cmd_factory_reset ="factory_reset"
    cmd_get_device_info ="get_device_info"
    cmd_get_network_info ="get_network_info"
    cmd_get_meter_attributes = "get_meter_attributes"
    cmd_set_meter_attributes ="set_meter_attributes"
    cmd_get_fast_poll_status="get_fast_poll_status"
    cmd_set_fast_poll="set_fast_poll"
    cmd_restarrt = "restart"
    cmd_get_current_summation_delivered="get_current_summation_delivered"
    cmd_get_instantaneous_demand ="get_instantaneous_demand"
    cmd_get_time ="get_time"
    cmd_get_current_summation = "get_current_summation"
    cmd_set_current_price ="set_current_price"
    cmd_set_meter_info = "set_meter_info"
    cmd_get_message ="get_message"
    cmd_confirm_message = "confirm_message"
    cmd_set_local_attributes="set_local_attributes"
    cmd_get_local_attributes="get_local_attributes"
    cmd_get_billing_periods="get_billing_periods"
    cmd_set_blk_price ="set_blk_price"
    cmd_set_price_block ="set_price_block"
    cmd_set_billing_period_list ="set_billing_period_list"
    cmd_set_billing_period="set_billing_period"
    cmd_get_price_blocks="get_price_blocks"
    cmd_set_block_structure ="set_block_structure"
    cmd_secret = "secret"
    cmd_get_schedule="get_schedule"
    cmd_get_profile_data="get_profile_data"
    cmd_get_schedule="get_schedule"
    cmd_set_schedule ="set_schedule"
    cmd_print_network_tables ="print_network_tables"
    cmd_image_block_dump = "image_block_dump"
    cmd_image_notify ="image_notify"
    cmd_image_block ="image_block"
    cmd_image_block_request ="image_block_request"
    cmd_image_invalidate_current= "image_invalidate_current"
    #device management details
    baud_rate = 115200
    port =0
    environment ="linux"
    windows_prefix = "COM"
    linux_prefix = "/dev/"
    osx_prefix = "/dev/"
    parity =serial.PARITY_NONE
    rtscts=0
    dsrdtr=0
    timeout=1
    bytesize=8
    print_string = True
    read_time = 15
    serial_attempt=0
    serial_connected = False
    illegal_xml_re = re.compile('[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf\ufffe-\uffff]')
    original_block = ""
    history=[]
    def __init__(self, port):
        self.port = port
        if platform.system()=='Windows':
            self.environment = "windows"
        elif platform.system()=="Darwin":
            self.environment= "osx"
    def restart(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_restart
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_device_info(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_device_info
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_network_info(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_network_info
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def factory_reset(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_factory_reset
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_restart_info(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_restart_info
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_restart_info(self, _type , confirm):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_restart_info
        self.command.append(self.command_name)
        self._type= copy.copy(self._type)
        self._type.text = _type
        self.confirm.text = confirm
        self.command.append(self._type)
        self.command.append(self.confirm)
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_meter_attributes(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_meter_attributes
        self.command.append(self.command_name)
    def set_meter_attributes(self, multiplier , divisor):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_meter_attributes
        self.multiplier.text = multiplier
        self.divisor.text = divisor
        self.command.append(self.command_name)
        self.command.append(self.multiplier)
        self.command.append(self.divisor)
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_fast_poll(self,frequency, duration):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_fast_poll
        self.frequency.text = frequency
        self.duration.text=duration
        self.command.append(self.command_name)
        self.command.append(self.frequency)
        self.command.append(self.duration)
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_fast_poll_status(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_fast_poll_status
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_current_price(self, refresh):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_current_price
        self.refresh.text = refresh
        self.command.append(self.command_name)
        self.command.append(self.refresh)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_current_price(price,currency ,trailing_digits):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_current_price
        self.currency.text = currency
        self.traling_digits.text = trailing_digits
        self.command.append(self.command_name)
        self.command.append(self.currency)
        self.command.append(self.trailing_digits)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_current_summation_delivered(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_current_summation_delivered
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_instantaneous_demand(self,refresh ):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_instantaneous_demand
        self.refresh.text = refresh
        self.command.append(self.command_name)
        self.command.append(self.refresh)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_time(self,refresh):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_time
        self.refresh.text = refresh
        self.command.append(self.command_name)
        self.command.append(self.refresh)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_current_price(self,price ,trailing_digits):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_current_price
        self.price.text = price
        self.trailing_digits.text = trailing_digits
        self.command.append(self.command_name)
        self.command.append(self.price)
        self.command.append(self.trailing_digits)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_meter_info(self,nickname,account,auth,host,enabled):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_current_price
        self.nickname.text = nickname
        self.account.text = account
        self.auth.text = auth
        self.host.text = host
        self.enabled.text = enabled
        self.command.append(self.command_name)
        self.command.append(self.nickname)
        self.command.append(self.account)
        self.command.append(self.auth)
        self.command.append(self.host)
        self.command.append(self.enabled)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_message(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_message
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_local_attributes(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_local_attributes
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_local_attributes(self,current_day_max_demand):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_local_attributes
        self.current_day_maximum_demand.text =current_day_max_demand
        self.command.append(self.command_name)
        self.command.append(self.current_day_maximum_demand)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_billing_periods(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_billing_periods
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_billing_period_list(self,number_of_billing_period ):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_billing_period_list
        self.number_of_periods.text=number_of_billing_period
        self.command.append(self.command_name)
        self.command.append(self.number_of_periods)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_billing_period(self, period, start):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_billing_period
        self.period.text=period
        self.start.text=start
        self.command.append(self.command_name)
        self.command.append(self.period)
        self.command.append(self.start)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_price_blocks(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_price_blocks
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_price_block(self,block,threshold,price ):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_price_block
        self.block.text=block
        self.threshold.text=threshold
        self.price.text=price
        self.command.append(self.command_name)
        self.command.append(self.block)
        self.command.append(self.threshold)
        self.command.append(self.price)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_schedule(self, mode):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_schedule
        self.mode.text=mode
        self.command.append(self.command_name)
        self.command.append(self.mode)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def get_profile_data(self, number_of_periods , interval_channel):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_get_profile_data
        self.number_of_periods.text=number_of_periods
        self.interval_channel.text=interval_channel
        self.command.append(self.command_name)
        self.command.append(self.interval_channel)
        self.command.append(self.number_of_periods)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def set_schedule(self,event,mode, frequency, enabled ):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_set_schedule
        if mode:
            self.mode.text=mode
            self.command.append(self.mode)
        if frequency:
            self.frequency.text=frequency
            self.command.append(self.frequency)
        if enabled:
            self.enabled.text=enabled
            self.command.append(self.enabled)
        self.event.text=event
        self.mode.text=mode
        self.event.text=event
        self.mode.text=mode
        self.event.text=event
        self.command.append(self.command_name)
        self.command.append(self.event)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def print_network_tables(self):
        self.command = copy.copy(self.command_root)
        self.command_name.text = self.cmd_print_network_tables
        self.command.append(self.command_name)
        #adding in the actual command
        self.write_buffer =etree.tostring(self.command, pretty_print=True)
        print(self.write_buffer)
    def create_serial(self):
        try:
            if self.environment =="osx":
                self.ser = serial.Serial(self.osx_prefix+str(self.port),self.baud_rate,timeout=self.timeout)
            elif self.environment == "linux":
                self.ser = serial.Serial(self.linux_prefix+str(self.port),self.baud_rate,timeout=self.timeout)
            else:
                self.ser = serial.Serial(self.windows_prefix+str(self.port),self.baud_rate,timeout=self.timeout)
            self.serial_connected =True
            self.serial_attempt=0
        except:
            if self.serial_attempt >3:
                print("Throwing an error, can't connect to EMU serial")
                raise
            else:
                self.serial_attempt = self.serial_attempt+1
                print("having trouble connecting to serial...."+str(self.serial_attempt))
                time.sleep(10)
    def serial_thread(self):
        self.stop_thread=False
        #this function is the thread which reads from the serial, writes to the serial and calls parsing functions
        print("Starting serial process for EMU on "+str(self.port))
        #inifinite loop
        try:
            self.create_serial()
            while True:
                if self.stop_thread is True:
                    self.ser.close()
                    print("Closing serial port for EMU")
                    #in case we was to stop thread
                    self.stop_thread=False
                    self.serial_connected=False
                    return
                else:
                    text =self.ser.readlines()
                    for line in text:
                        linex = line.decode()
                        #print(linex)
                        self.serial_reader(linex)
                    if self.write_buffer is not None:
                        try:
                            f =open('static/emu-log.txt','a')
                            f.write(self.write_buffer.translate(None, "<>\\"))
                            f.write('\n')
                            f.close()
                        except:
                            pass
                        self.ser.write(self.write_buffer)
                        self.write_history('HOST', self.command_name.text, self.write_buffer, None)
                        self.write_buffer = None
                        time.sleep(0.1)
        except:
            raise
    def start_serial(self):
        self.thread_handle = threading.Thread(target=self.serial_thread, args=[])
        self.thread_handle.start()
    def stop_serial(self):
        self.stop_thread= True
    def parse_response(self,response):
        self.response = str(illegal_xml_re.sub('', response))
        self.reponse_root =etree.fromstring(self.response)
        for child in self.response:
            self.tree = objectify.Element(root)
        #self.tree = etree.fromstring()
    def look_for_start_tag(self,line):
        #this reads eachline looking for a start tag
        start_tag = False
        #these are thetags that are possible
        for tag in self.responseRoots:
            tagToString = '<'+tag+'>'
            if  tagToString in line:
                    start_tag=True;
                    self.tag = tag
        return start_tag
    def look_for_end_tag(self,line):
        #this reads eachline looking for a start tag
        end_tag = False
        #these are thetags that are possible
        tagToString = '</'+self.tag+'>'
        #checking if tag is in line
        if tagToString in line:
            end_tag=True
        return end_tag
    def serial_reader(self,line):
        #this function is reads the text
        self.start_flag=False
        if self.look_for_start_tag(line):
            self.tag_block=True
            self.start_flag=True
        if self.tag_block ==True:
            self.original_block = self.original_block+line
            self.block_string = self.block_string+line.rstrip()
        if self.look_for_end_tag(line):
            self.tag_block = False
            try:
                self.block_to_tree(self.block_string,self.tag)
            except Exception as e:
                print(str(e))
                print("XML ISSUE")
                obj =dict()
                # self.block_string
            self.block_string=""
            self.original_block = ""
        self.start_flag=False
    def block_to_tree(self,block_string,tag):
        #print "converting string"
        block_string = self.illegal_xml_re.sub('', block_string)
        if tag in self.responseRoots:
            self.xmlTree =objectify.fromstring(block_string)
            module = __import__('api_classes')
            class_ = getattr(module, tag)
            instance = class_(self.xmlTree, self.original_block)
            setattr(self, tag, instance)
            self.write_history('EMU', tag, self.original_block, instance)
        self.state[tag] = dict()
        for element in self.xmlTree.iter():
            self.data[element.tag] = element.text
            self.state[tag][element.tag]=element.text
        for tag in self.responseRoots:
            try:
                del self.data[tag]
            except:
                pass
    def write_history(self,origin, tag, raw, dict_):
        history_obj ={
            'origin':origin,
            'type':tag,
            'obj':dict_,
            'raw': raw
        }
        
        self.history.append(history_obj)
    def readback(self, limit=100):
        limit_count = 0
        for item in reversed(self.history):
            print("SENT BY :"+str(item['origin']))
            print("TYPE OF :"+str(item['type']))
            print("RAW DATA:-------------------       ")
            print(str(item['raw']))
            #print str(type(recursive_dict(self.xmlTree.getroot())))
            limit_count +=1
            if limit_count >limit:
                break
    def clear_history():
        self.history=[]

        
if __name__ == '__main__':
    emu_instance = emu('tty.usbmodemfd121')
    emu_instance.start_serial()
    emu_instance.get_current_summation_delivered()
    time.sleep(5)
    emu_instance.stop_serial()
    print(emu_instance.CurrentSummationDelivered)
    print(emu_instance.CurrentSummationDelivered.SummationDelivered)
    for hist in emu_instance.history:
        print(hist)

