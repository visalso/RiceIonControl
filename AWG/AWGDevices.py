'''
Created on Jul 2, 2015

@author: Geoffrey Ji

AWG Devices are defined here. If a new AWG needs to be added,
it must inherit AWGDeviceBase and implement:

- __init__
   to initialize whatever libraries it needs

- open, program, trigger, and close
   to interface with the AWG

- deviceProperties
   To specify fixed properties of the AWG device. Required keys:

    - minSamples (int)
       minimum number of samples to program

    - maxSamples (int)
       maximum number of samples to program

    - sampleChunkSize (int)
       number of samples must be a multiple of sampleChunkSize

    - padValue (int)
       the waveform will be padded with this number to make it a multiple of sampleChunkSize, or to make it the length of minSamples

    - minAmplitude (int)
       minimum amplitude value (raw)

    - maxAmplitude (int)
       maximum amplitude value (raw)

    - numChannels (int)
       Number of channels

    - calibration (function)
        function that returns raw amplitude number, given voltage

    - calibrationInv (function)
        function that returns voltage, given raw amplitude number

- parameters
   To define dynamic properties and actions of the AWG, which are shown in the GUI and can be modified in the program.
'''

import inspect
import logging
import socket  # for TCP communication
import struct  # for TCP message formatting
import sys
import time
import ctypes
import _ctypes
import copy
import warnings
from modules.quantity import Q
from ctypes import *
sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')     # Keysight AWG
try:
    import keysightSD1
except ImportError:
    print("INFO: No Keysight AWG Module!")
import numpy
from multiprocessing import Pool

from AWG.AWGSegmentModel import AWGSegmentNode
from ProjectConfig.Project import getProject
from modules.Expression import Expression
#from modules.magnitude import new_mag
from modules.SequenceDict import SequenceDict
from uiModules.ParameterTable import Parameter


class AWGDeviceBase(object):
    """base class for AWG Devices"""
    expression = Expression()
    def __init__(self, settings):
        self.settings = settings
        self.settings.deviceSettings.setdefault('programOnScanStart', False)
        self.settings.deviceSettings.setdefault('reprogramOnScanSteps', False)
        self.settings.deviceSettings.setdefault('preprocessWaveforms', False)
        self.settings.deviceSettings.setdefault('useCalibration', False)
        self.waveforms = []
        for channel in range(self.deviceProperties['numChannels']):
            self.waveforms.append(None)
            if channel >= len(self.settings.channelSettingsList): #create new channels if it's necessary
                self.settings.channelSettingsList.append({'segmentDataRoot':AWGSegmentNode(None, ''),
                                                          'segmentTreeState':None,
                                                          'plotEnabled' : True,
                                                          'plotStyle':self.settings.plotStyles.lines})
        self.project = getProject()
        awgConfigDict = list(self.project.hardware[self.displayName].values())[0]
        sampleRateText = awgConfigDict['sampleRate']
        sampleRate = self.expression.evaluateAsMagnitude(sampleRateText)
        self.deviceProperties['sampleRate'] = sampleRate
        sample = 1/self.deviceProperties['sampleRate']
        #new_mag('sample', sample)  # TODO: check whether the added samples = count / second in modules/quantity_units.txt
        #new_mag('samples', sample)  # replaces this
        if not self.project.isEnabled('hardware', self.displayName):
            self.enabled = False
        else:
            self.open()

    def parameters(self):
        """return the parameter definitions used by the parameterTable to show the gui"""
        return SequenceDict(
            [( 'Use Calibration', Parameter(name='Use Calibration', dataType='bool', value=self.settings.deviceSettings['useCalibration'], key='useCalibration') ),
             ( 'Program on scan start', Parameter(name='Program on scan start', dataType='bool', value=self.settings.deviceSettings['programOnScanStart'], key='programOnScanStart') ),
             ( 'Reprogram on scan steps', Parameter(name='Reprogram on scan steps', dataType='bool', value=self.settings.deviceSettings['reprogramOnScanSteps'], key='reprogramOnScanSteps') ),
             ( 'Preprocess Waveforms', Parameter(name='Preprocess Waveforms', dataType='bool', value=self.settings.deviceSettings['preprocessWaveforms'], key='preprocessWaveforms') ),
             ( 'Program now', Parameter(name='Program now', dataType='action', value='program') ),
             ( 'Trigger now', Parameter(name='Trigger now', dataType='action', value='trigger') )] )

    def update(self, parameter):
        """update the parameter, called by the parameterTable"""
        if parameter.dataType!='action':
            self.settings.deviceSettings[parameter.key] = parameter.value
            self.settings.saveIfNecessary()
            if parameter.key=='useCalibration':
                self.settings.replot()
        else:
            getattr(self, parameter.value)()

    #functions and attributes that must be defined by inheritors
    def open(self): raise NotImplementedError("'open' method must be implemented by specific AWG device class")
    def program(self): raise NotImplementedError("'program' method must be implemented by specific AWG device class")
    def trigger(self): raise NotImplementedError("'trigger' method must be implemented by specific AWG device class")
    def close(self): raise NotImplementedError("'close' method must be implemented by specific AWG device class")
    @property
    def deviceProperties(self): raise NotImplementedError("'deviceProperties' must be set by specific AWG device class")
    @property
    def displayName(self): raise NotImplementedError("'displayName' must be set by specific AWG device class")


class Lecroy1102(AWGDeviceBase):
    """Class for programming a Lecroy 1102 AWG"""
    displayName = "Lecroy 1102 AWG"
    deviceProperties = dict(
        minSamples = 8, #minimum number of samples to program
        maxSamples = 2000000, #maximum number of samples to program
        sampleChunkSize = 2, #number of samples must be a multiple of sampleChunkSize
        padValue = 0, #the waveform will be padded with this number to make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 1.5, #maximum amplitude value (raw)
        numChannels = 2, #Number of channels
        calibration = lambda voltage: voltage, #function that returns raw amplitude number, given voltage
        calibrationInv = lambda raw: raw #function that returns voltage, given raw amplitude number

        # program project hardware properties specified in the .yml file
        #   sampleRate = mg(244.258800, 'MHz'), #rate at which the samples programmed are output by the AWG
        #   external_clock_frequency = mg(81419600, 'Hz'), #rate at which the AWG is clocked
    )

    def parameters(self):
        """return the parameter definition used by the ParameterTable to show the gui"""
        parameterDict = super(Lecroy1102, self).parameters()
        name='Open connection and configure'
        parameterDict[name] = Parameter(name=name, dataType='action', value='open')
        name = 'Close connection'
        parameterDict[name] = Parameter(name=name, dataType='action', value='close')
        return parameterDict

    def send(self, command_string):

       		# Send a well formatted message to the server.
            # The server must be running, and this instance must already have called connect().
            # Each message begins with MESG,
            # followed by 4 bytes (a 32 bit unsigned long integer) that give the length of the rest of the message,
            # followed by the rest of the message (command_string).

            # find the length of the command_string
            length = len(command_string)
            if length>=4294967296: #2**32
                logging.getLogger(__name__).error('Lecroy AWG TCP message is too long, size = '+str(length)+' bytes')

            # format the message
            message = b'MESG'+struct.pack("!L", length)+command_string

            # send the message
            self.sock.sendall(message)

    def open(self):
        logger = logging.getLogger(__name__)
        try:

            # set up TCP connection
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Open a connection to the TCP server.
            # The server should already be running at the given IP address.
            # The port numbers must agree between the client and server.
            IP_address_string = list(self.project.hardware[self.displayName].values())[0]['ipAddress']
            port_number = list(self.project.hardware[self.displayName].values())[0]['port']
            self.sock.connect((IP_address_string, port_number))

            # message format:
            # MESG
            # 4 byte data length
            # CONF
            # command_string:
            #   4 byte command name
            #     4 byte command length
            #     command data
            #  repeat until done

            # start with a blank command string
            command_string = b'CONF'

            # sample rate: 4 byte command + 8 byte double
            command_string += b'rate'
            sampleRate_Hz = self.deviceProperties['sampleRate'].m_as('Hz')
            # convert double to byte encoding, and append to message
            command_string += struct.pack('!d', sampleRate_Hz)

            # external_clock_frequency: 4 byte command + 8 byte double
            command_string += b'eclk'
            external_clock_frequency_in = list(self.project.hardware[self.displayName].values())[0]['extClockFrequency']
            external_clock_frequency = self.expression.evaluateAsMagnitude(external_clock_frequency_in).m_as('Hz')
            # convert double to byte encoding, and append to message
            command_string += struct.pack('!d', external_clock_frequency)

            self.send(command_string)

            self.enabled = True
            logger.info("Successfully opened {0}".format(self.displayName))
        except Exception as e:
            logger.error("Unable to open {0}: {1}".format(self.displayName, e))
            self.enabled = False

    def program(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            channel_0_Points = self.waveforms[0].evaluate()  # this is a 1D numpy array
            channel_1_Points = self.waveforms[1].evaluate()  # this is a 1D numpy array
            logger.info("channel_0_Points.dtype:"+str(channel_0_Points.dtype))
            logger.info("channel_1_Points.dtype:"+str(channel_1_Points.dtype))
            logger.info( "writing {0} points to AWG channel 0".format(len(channel_0_Points)) )
            logger.info( "writing {0} points to AWG channel 1".format(len(channel_1_Points)) )

            # send waveforms over TCP to Lecroy C# server

            command_string = b'UPDA'
            command_string += struct.pack('!L', len(channel_0_Points))
            command_string += channel_0_Points.astype('<f8').tobytes()
            command_string += struct.pack('!L', len(channel_1_Points))
            command_string += channel_1_Points.astype('<f8').tobytes()

            self.send(command_string)

            time.sleep(1.5)  # wait 1.5 second for AWG programming to complete

        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.displayName))

    def trigger(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            # SEND COMMAND TO TRIGGER AWG
            self.send('TRIG')
            logger.info("Triggered {0}".format(self.displayName))

    def close(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            # close the TCP connection to the AWG server
            self.sock.close()
            logger.info("Connection to {0} closed".format(self.displayName))

class ChaseDA12000(AWGDeviceBase):
    """Class for programming a ChaseDA12000 AWG"""
    displayName = "Chase DA12000 AWG"
    deviceProperties = dict(
        minSamples = 128, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 64, #number of samples must be a multiple of sampleCnunkSize
        padValue = 2047, #the waveform will be padded with this number to make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095, #maximum amplitude value (raw)
        numChannels = 1, #Number of channels
        calibration = lambda voltage: 2047. + 3413.33*voltage, #function that returns raw amplitude number, given voltage
        calibrationInv = lambda raw: -0.599707 + 0.000292969*raw #function that returns voltage, given raw amplitude number
    )

    class SEGMENT(Structure):
        _fields_ = [("SegmentNum", c_ulong),
                    ("SegmentPtr", POINTER(c_ulong)),
                    ("NumPoints", c_ulong),
                    ("NumLoops", c_ulong),
                    ("BeginPadVal ", c_ulong), # Not used
                    ("EndingPadVal", c_ulong), # Not used
                    ("TrigEn", c_ulong),
                    ("NextSegNum", c_ulong)]

    def __init__(self, settings):
        self.project = getProject()
        self.settings = settings
        if not self.project.isEnabled('hardware', self.displayName):
            self.enabled = False
        else:
            dllName = list(self.project.hardware[self.displayName].values())[0]['DLL']
            try:
                self.lib = WinDLL(dllName)
                self.enabled = True
            except Exception:
                logging.getLogger(__name__).info("{0} unavailable. Unable to open {1}.".format(self.displayName, dllName))
                self.enabled = False
        self.settings.deviceSettings.setdefault('continuous', False)
        super(ChaseDA12000, self).__init__(settings)

    def parameters(self):
        """return the parameter definition used by the ParameterTable to show the gui"""
        parameterDict = super(ChaseDA12000, self).parameters()
        name='Run continuously'
        parameterDict[name] = Parameter(name=name,
                                        dataType='bool',
                                        value=self.settings.deviceSettings['continuous'],
                                        tooltip="Restart sequence at sequence end, continuously (no trigger)",
                                        key='continuous')
        return parameterDict

    def open(self):
        logger = logging.getLogger(__name__)
        try:
            self.lib.da12000_Open(1)
            self.enabled = True
        except Exception:
            logger.info("Unable to open {0}.".format(self.displayName))
            self.enabled = False
    
    def program(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            pts = self.waveforms[0].evaluate()
            if self.settings.deviceSettings.get('useCalibration'):
                calibration = self.settings.deviceProperties['calibration']
                calibration = numpy.vectorize(calibration, otypes=[numpy.int])
                pts = calibration(pts)
            pts.tolist()
            logger.info("writing " + str(len(pts)) + " points to AWG")
            seg_pts = (c_ulong * len(pts))(*pts)
            seg0 = self.SEGMENT(0, seg_pts, len(pts), 0, 2048, 2048, 1, 0)
            seg = (self.SEGMENT*1)(seg0)

            self.lib.da12000_CreateSegments(1, 1, 1, seg)
            self.lib.da12000_SetTriggerMode(1, 1 if self.settings.deviceSettings['continuous'] else 2, 0)
        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.displayName))

    def trigger(self):
        if self.enabled:
            self.lib.da12000_SetSoftTrigger(1)

    def close(self):
        if self.enabled:
            self.lib.da12000_Close(1)

class KeysightM3202A(AWGDeviceBase):
    """Class for programming an Keysight M3202A AWG"""
    displayName = "Keysight M3202A AWG"
    deviceProperties = dict(
        minSamples = 30, #minimum number of samples to program
        maxSamples = 10**9, #maximum number of samples to program
        minAmplitude = -0.5, #minimum amplitude value (raw) NOTE: THIS IS ONLY THE DEFAULT VALUE
        maxAmplitude = 0.5, #maximum amplitude value (raw) NOTE: THIS IS ONLY THE DEFAULT VALUE
        numChannels = 4, #Number of channels
        sampleChunkSize = 1,
        padValue = 0,
        # displayName = "Keysight M3202A AWG",
        calibration = lambda voltage: voltage, #function that returns raw amplitude number, given voltage
        calibrationInv = lambda raw: raw, #function that returns voltage, given raw amplitude number
    )

    def __init__(self, settings):
        self.settings = settings
        self.settings.deviceSettings.setdefault('programOnScanStart', False)
        self.settings.deviceSettings.setdefault('reprogramOnScanSteps', False)
        self.settings.deviceSettings.setdefault('preprocessWaveforms', False)
        self.settings.deviceSettings.setdefault('useCalibration', False)
        self.settings.deviceSettings.setdefault('voltlimit', "0.5 V")
        self.waveforms = []
        for channel in range(self.deviceProperties['numChannels']):
            self.waveforms.append(None)
            if channel >= len(self.settings.channelSettingsList): #create new channels if it's necessary
                self.settings.channelSettingsList.append({'segmentDataRoot':AWGSegmentNode(None, ''),
                                                          'segmentTreeState':None,
                                                          'plotEnabled' : True,
                                                          'plotStyle':self.settings.plotStyles.lines})
        self.project = getProject()
        awgConfigDict = list(self.project.hardware[self.displayName].values())[0]
        self.chassis_addr = awgConfigDict['Chassis']
        sampleRate = self.expression.evaluateAsMagnitude("1 GHz")
        self.deviceProperties['sampleRateScalar'] = sampleRate.m_as('Hz')
        self.deviceProperties['sampleRate'] = sampleRate
        self.slot_addr = awgConfigDict['Slot']
        self._initialized = False
        self.preloaded_wave_data_1 = []
        self.preloaded_wave_data_2 = []
        self.preloaded_wave_data_3 = []
        self.preloaded_wave_data_4 = []
        self.module = keysightSD1.SD_AOU()

    def parameters(self):
        """return the parameter definition used by the ParameterTable to show the gui"""
        parameterDict = super(KeysightM3202A, self).parameters()
        name='Voltage Limit - Do not Exceed 0.999...'
        parameterDict[name] = Parameter(name=name, dataType='magnitude', value=self.settings.deviceSettings['voltlimit'],
                                        tooltip="Limit KeySight AWG to this maximum voltage to protect AOMs",
                                        key='voltlimit')
        name='Reinitialize AWG'
        parameterDict[name] = Parameter(name=name, dataType='action', value='initialize')
        return parameterDict

    def initialize(self):

        if self._initialized:
            self.close()

        PRODUCT = ""
        CHASSIS = self.chassis_addr
        SLOT = self.slot_addr
        AMPLITUDE = 1.28

        moduleID = self.module.openWithSlot(PRODUCT, CHASSIS, SLOT)

        if moduleID < 0:
            print("Module open error:", moduleID)
            print("Error: Cannot Open Keysight AWG!")
            self._initialized = False
        else:
            print("Keysight AWG successfully opened with Module ID: %s and Module name: %s"
                  %(moduleID, self.module.getProductName()))
            self.module.waveformFlush()                                 # Clear any old waveforms from the RAM
            self.module.clockIOconfig(1)                                # Enable Clock
            for CHANNEL in [1,2,3,4]:
                self.module.channelOffset(CHANNEL, 0)
                self.module.AWGqueueConfig(CHANNEL, 1)
                self.module.channelWaveShape(CHANNEL, keysightSD1.SD_Waveshapes.AOU_AWG)
                self.module.channelAmplitude(CHANNEL, AMPLITUDE)
                self.module.AWGtriggerExternalConfig(CHANNEL, 0, 3, 0)  # Wait for external trigger after programming
            self._initialized = True

    def preprocess_waves(self, wave1):
        wave1 = numpy.append(wave1, [0] * 10)   # Padding to ensure no clipping of important waveform
        wave = keysightSD1.SD_Wave()
        wave.newFromArrayDouble(keysightSD1.SD_WaveformTypes.WAVE_ANALOG, numpy.array(wave1))
        return wave

    def send_wave(self, wave, CHANNEL):
        self.module.waveformLoad(wave, CHANNEL, 0)
        self.module.AWGqueueWaveform(CHANNEL, CHANNEL, 6, 0, 1, 0)
        self.module.AWGstart(CHANNEL)

    def open(self):
        if self._initialized == False:
            self.initialize()

    def close(self):
        self.module.close()
        self._initialized = False

    def trigger(self):
        logger = logging.getLogger(__name__)
        if self._initialized == False:
            self.initialize()
        for CHANNEL in [1,2,3,4]:
            self.module.AWGtrigger(CHANNEL)
        logger.info("Keysight AWG Software Trigger Sent")

    def program(self):
        logger = logging.getLogger(__name__)
        if self._initialized == False:
            self.initialize()
        wave1_raw = self.waveforms[0].evaluate()
        wave2_raw = self.waveforms[1].evaluate()
        wave3_raw = self.waveforms[2].evaluate()
        wave4_raw = self.waveforms[3].evaluate()
        wave1 = self.preprocess_waves(wave1_raw)
        wave2 = self.preprocess_waves(wave2_raw)
        wave3 = self.preprocess_waves(wave3_raw)
        wave4 = self.preprocess_waves(wave4_raw)
        self.send_wave(wave1, 1)
        self.send_wave(wave2, 2)
        self.send_wave(wave3, 3)
        self.send_wave(wave4, 4)
        logger.info("Keysight AWG Programmed")

    def immediate_program(self, step):
        if self._initialized == False:
            self.initialize()
        self.send_wave(self.preloaded_wave_data_1[step], 1)
        self.send_wave(self.preloaded_wave_data_2[step], 2)
        self.send_wave(self.preloaded_wave_data_3[step], 3)
        self.send_wave(self.preloaded_wave_data_4[step], 4)

    def Unload_data(self):              # Clear preloaded_wave_data variable
        self.preloaded_wave_data_1 = []
        self.preloaded_wave_data_2 = []
        self.preloaded_wave_data_3 = []
        self.preloaded_wave_data_4 = []

    def Preload(self):
        wave1_raw = self.waveforms[0].evaluate()
        wave2_raw = self.waveforms[1].evaluate()
        wave3_raw = self.waveforms[2].evaluate()
        wave4_raw = self.waveforms[3].evaluate()
        wave1 = self.preprocess_waves(wave1_raw)
        wave2 = self.preprocess_waves(wave2_raw)
        wave3 = self.preprocess_waves(wave3_raw)
        wave4 = self.preprocess_waves(wave4_raw)
        self.preloaded_wave_data_1.append(wave1)
        self.preloaded_wave_data_2.append(wave2)
        self.preloaded_wave_data_3.append(wave3)
        self.preloaded_wave_data_4.append(wave4)

class DummyAWG(AWGDeviceBase):
    displayName = "Dummy AWG"
    deviceProperties = dict(
        minSamples = 1, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 1, #number of samples must be a multiple of sampleChunkSize
        padValue = 2047, #the waveform will be padded with this number ot make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095, #maximum amplitude value (raw)
        numChannels = 2,  #Number of channels
        calibration = lambda voltage: 2047. + 3413.33*voltage, #function that returns raw amplitude number, given voltage
        calibrationInv = lambda raw: -0.599707 + 0.000292969*raw #function that returns voltage, given raw amplitude number
    )
    
    def open(self): pass
    def initialize(self): pass
    def close(self): pass
    def trigger(self):
        logger = logging.getLogger(__name__)
        logger.info("Dummy AWG Trigger signal")
    def program(self):
        logger = logging.getLogger(__name__)
        pts0 = self.waveforms[0].evaluate()
        pts1 = self.waveforms[1].evaluate()
        if self.settings.deviceSettings.get('useCalibration'):
            calibration = self.settings.deviceProperties['calibration']
            calibration = numpy.vectorize(calibration, otypes=[numpy.int])
            pts0 = calibration(pts0)
            pts1 = calibration(pts1)
        pts0.tolist()
        pts1.tolist()
        logger.info("points to write to AWG channel 0: " + str(len(pts0)))
        logger.info("points to write to AWG channel 1: " + str(len(pts1)))


# class TaborAWG(AWGDeviceBase):
#     displayName = "Tabor AWG"
#     deviceProperties = dict(
#         minSamples=1,  # minimum number of samples to program
#         maxSamples=4000000,  # maximum number of samples to program
#         sampleChunkSize=1,  # number of samples must be a multiple of sampleChunkSize
#         padValue=2047,
#         # the waveform will be padded with this number ot make it a multiple of sampleChunkSize, or to make it the length of minSamples
#         minAmplitude=0,  # minimum amplitude value (raw)
#         maxAmplitude=4095,  # maximum amplitude value (raw)
#         numChannels=2,  # Number of channels
#         calibration=lambda voltage: 2047. + 3413.33 * voltage,
#         # function that returns raw amplitude number, given voltage
#         calibrationInv=lambda raw: -0.599707 + 0.000292969 * raw
#         # function that returns voltage, given raw amplitude number
#     )
#
#     def open(self): pass
#
#     def close(self): pass
#
#     def trigger(self):
#         logger = logging.getLogger(__name__)
#         logger.info("Tabor AWG Trigger signal")
#
#     def program(self):
#         logger = logging.getLogger(__name__)
#         pts0 = self.waveforms[0].evaluate()
#         pts1 = self.waveforms[1].evaluate()
#         if self.settings.deviceSettings.get('useCalibration'):
#             calibration = self.settings.deviceProperties['calibration']
#             calibration = numpy.vectorize(calibration, otypes=[numpy.int])
#             pts0 = calibration(pts0)
#             pts1 = calibration(pts1)
#         pts0.tolist()
#         pts1.tolist()
#         logger.info("points to write to AWG channel 0: " + str(len(pts0)))
#         logger.info("points to write to AWG channel 1: " + str(len(pts1)))



def isAWGDevice(obj):
    """Determine if obj is an AWG device.
    returns True if obj inherits from AWGDeviceBase, but is not itself AWGDeviceBase"""
    try:
        inheritance = inspect.getmro(obj)
        return True if AWGDeviceBase in inheritance and AWGDeviceBase!=inheritance[0] else False
    except:
        return False

#Extract the AWG device classes
current_module = sys.modules[__name__]
AWGDeviceClasses = inspect.getmembers(current_module, isAWGDevice)
AWGDeviceDict = {cls.displayName:clsName for clsName, cls in AWGDeviceClasses}
