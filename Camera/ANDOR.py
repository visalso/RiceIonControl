#!/usr/bin/python
# -*- coding: latin-1 -*-
"""High level interface to Andor iXon+ emCCD camera."""

import numpy
from ctypes import *
from time import *
import time
import os

dllpath = os.path.join(os.path.dirname(__file__), '..', 'Camera/atmcd64d')
# print(dllpath)
windll.LoadLibrary(dllpath)

# If no camera is connected, set DEBUG_MODE to True so that the program will create fake images
DEBUG_MODE = False

# hack to releas GIL during wait
# MVll = ctypes.windll.mvDeviceManager
# llWait = MVll.DMR_ImageRequestWaitFor
# llWait.argtypes = [ctypes.c_int,
# ctypes.c_int,
# ctypes.c_int,
# ctypes.POINTER(ctypes.c_int)]
# llWait.restype = ctypes.c_int

class NoCamError(Exception):
    def __init__(self):
        Exception.__init__(self, 'No Camera')


class CamTimeoutError(Exception):
    def __init__(self):
        super(CamTimeoutError, self).__init__(self, 'Timeout')


class TimeoutError(Exception):
    def __init__(self):
        Exception.__init__(self, 'Timeout')


class Cam(object):

    def __init__(self):
        self.andormode = 'Live'
        self.width = 0
        self.height = 0
        self.numberandorimages = 0
        self.hStart = 1
        self.hEnd = 512
        self.vStart = 1
        self.vEnd = 512
        windll.atmcd64d.Initialize(".")
        camsn = c_long()
        windll.atmcd64d.GetCameraSerialNumber(byref(camsn))
        if camsn.value == 0:
            self.error = True
            print("Andor not available Cam")
        else:
            self.error = False
            print("Andor initialized")
            print('Andor camera s/n:', camsn.value)

    def open(self):
        print('Andor open')
        windll.atmcd64d.SetTriggerMode(1)  # 1=external, 0=internal
        windll.atmcd64d.SetReadMode(4)  # read images
        windll.atmcd64d.SetShutter(0, 1, 0, 0)  # Shutter open
        windll.atmcd64d.SetFrameTransferMode(0)
        windll.atmcd64d.SetHSSpeed(0, 0)
        index = c_int()
        speed = c_float()
        Vspeed = c_float()

        windll.atmcd64d.GetFastestRecommendedVSSpeed(byref(index), byref(speed))

        valid=windll.atmcd64d.SetVSSpeed(index)
        if valid == 20002: print("successful SetVSSpeed")
        else: print('SetVSSpeed = ',valid)

        windll.atmcd64d.GetVSSpeed(index,byref(Vspeed))
        windll.atmcd64d.SetVSAmplitude(0)

        print('{index, speed, VSpeed}:', index.value,',', speed.value,',', Vspeed.value)
        return self

    def close(self):
        print('Andor close')

    def shutdown(self):
        windll.atmcd64d.ShutDown()
        print('Andor shutdown')

    def stop(self):
        print('Andor stop')
        windll.atmcd64d.AbortAcquisition()
        windll.atmcd64d.SetShutter(0, 1, 0, 0) # 0 Low=open, 1 shutter to be permanently open

    def gettemperature(self):
        """Get temperature of CCD"""
        temperature = c_float()
        windll.atmcd64d.GetTemperatureF(byref(temperature))
        return temperature.value

    def wait(self, timeout = 10):
        """Check if new image is available, and waits for specified time. Raises CamTimeoutError if no new image
        available."""

        time.sleep(timeout)  # --------------------------------#
        status = c_int()
        currentnumberimages = c_int()
        windll.atmcd64d.GetTotalNumberImagesAcquired(byref(currentnumberimages))
        print("currentnumberimages = ", currentnumberimages.value)

        if self.andormode == 'Live' or self.andormode == 'AutoLoad':
            if currentnumberimages.value != self.numberandorimages:
                print('Image #', currentnumberimages.value)
                self.numberandorimages = currentnumberimages.value
            else:
                raise CamTimeoutError
        if self.andormode == 'TriggeredAcquisition_1':
            windll.atmcd64d.GetStatus(byref(status))
            print("status = ", status.value)
            if status.value == 20073:
                self.numberandorimages = currentnumberimages.value
            else:
                raise CamTimeoutError

    def start_cooling(self, setPoint = -60):
        tmin = c_int()
        tmax = c_int()
        windll.atmcd64d.GetTemperatureRange(byref(tmin), byref(tmax))
        # windll.atmcd64d.SetTemperature(tmin.value)
        windll.atmcd64d.SetTemperature(setPoint)
        windll.atmcd64d.CoolerON()
        print("Andor start cooling")
        # print('  set min temp = ', tmin.value)
        print('  set min temp = ', setPoint)

    def stop_cooling(self):
        windll.atmcd64d.CoolerOFF()
        print("Andor stop cooling")
        print("temp = ", self.gettemperature())

    def frame_height(self):
        xsize = c_long()
        ysize = c_long()
        windll.atmcd64d.GetDetector(byref(xsize), byref(ysize))
        return ysize.value

    def frame_width(self):
        xsize = c_long()
        ysize = c_long()
        windll.atmcd64d.GetDetector(byref(xsize), byref(ysize))
        return xsize.value

    def set_timing(self, integration = 100, repetition = 0, ampgain = 0, emgain = 0, numExp = 1, numScan = 1, emgainAdv = 0):
        print('Andor Imaging mode: ', self.andormode)
        fakeim = 50 if DEBUG_MODE else 0
        # ==============================In normal operation set fakeim=0, just for debugging====================================

        # 0 internal 1 external 7 external exposure 10 software trigger
        self.width = self.frame_width() + fakeim
        self.height = self.frame_height() + fakeim
        if self.width <= 0 or self.height <= 0:
            raise NoCamError
        triggerMode = None
        acquisitionMode = None
        hBin = 1
        vBin = 1
        hTrim = 0
        vTrim = 0

        repetition = 0
        emGainUse = 0
        emAdvMode = 0
        highcapacity=0
        if self.andormode == 'FastKinetics':
            print('Setting camera parameters for fast kinetics.')
            # self.width = self.frame_width() + fakeim
            # self.height = self.frame_height() + fakeim
            # windll.atmcd64d.SetAcquisitionMode(4)  # 1 single mode 2 accumulate mode 5 run till abort
            # windll.atmcd64d.SetFastKinetics(501,2,c_float(3.0e-3),4,1,1)
            acquisitionMode = 4
            triggerMode = 0
            emGainUse = emgain
            emAdvMode = 0

            windll.atmcd64d.SetFastKinetics(501, 2, c_float(integration * 1.0e-3), 4, 1, 1)
        elif self.andormode == 'Live' or self.andormode == 'AutoLoad':
            print('Setting camera parameters for live mode.')
            # self.width = self.frame_width() + fakeim
            # self.height = self.frame_height() + fakeim
            # windll.atmcd64d.SetAcquisitionMode(5)  # 1 single mode 2 accumulate mode 5 run till abort
            acquisitionMode = 5
            triggerMode = 0
            windll.atmcd64d.SetTriggerMode(triggerMode)
            windll.atmcd64d.SetAcquisitionMode(acquisitionMode)

            emGainUse = emgain
            emAdvMode = 0

            #windll.atmcd64d.SetEMAdvanced(0)

        elif self.andormode == 'TriggeredAcquisition' :
            print('Setting camera parameters for Triggered Acquisition mode')
            print('Andor.set_timing: numExp = ',numExp)
            # windll.atmcd64d.SetAcquisitionMode(5)  # 1 single mode 2 accumulate mode 5 run till abort
            acquisitionMode = 3
            triggerMode = 7
            print("triggerMode = ",triggerMode)
            windll.atmcd64d.SetTriggerMode(triggerMode)
            windll.atmcd64d.SetAcquisitionMode(acquisitionMode)

            valid=windll.atmcd64d.SetNumberKinetics(numExp)
            if valid == 20002: print("successful SetNumberKinetics")
            else: print('SetNumberKinetics = ',valid)

            valid=windll.atmcd64d.SetNumberAccumulations(1)
            if valid == 20002: print("successful SetNumberAccumulations")
            else: print('SetNumberAccumulations = ',valid)

            emGainUse = emgainAdv
            emAdvMode = 1
            highcapacity=1

        elif  self.andormode == 'Detecter':
            print('Setting camera parameters for Detecter Acquisition mode')
            print('Andor.set_timing: numExp = ',numExp)
            # windll.atmcd64d.SetAcquisitionMode(5)  # 1 single mode 2 accumulate mode 5 run till abort
            acquisitionMode = 3
            triggerMode = 0
            print("triggerMode = ",triggerMode)
            windll.atmcd64d.SetTriggerMode(triggerMode)
            windll.atmcd64d.SetAcquisitionMode(acquisitionMode)

            valid=windll.atmcd64d.SetNumberKinetics(numExp)
            if valid == 20002: print("successful SetNumberKinetics")
            else: print('SetNumberKinetics = ',valid)

            valid=windll.atmcd64d.SetNumberAccumulations(1)
            if valid == 20002: print("successful SetNumberAccumulations")
            else: print('SetNumberAccumulations = ',valid)
            #windll.atmcd64d.SetEMAdvanced(0)

            # print('Set FTCCD Code:', windll.atmcd64d.SetFrameTransferMode(1))

            emGainUse = emgain
            emAdvMode = 0


        else:
            acquisitionMode = 5
            triggerMode = 0

        print('Andor set timings:')
        print('  set exposure time =', integration, 'ms')
        print('  set repetition time =', repetition, 'ms')

        cExp = c_float(integration * 1.0e-3)
        windll.atmcd64d.SetExposureTime(cExp)

        print('SetImg Code:', windll.atmcd64d.SetImage(hBin, vBin,
                                                       self.hStart , self.hEnd,
                                                       self.vStart , self.vEnd))
        #print('SetImg Code:', windll.atmcd64d.SetImage(hBin, vBin, hStart, hEnd, vStart, vEnd))
        self.effWidth = self.hEnd - self.hStart + 1
        self.effHeight = self.vEnd - self.vStart + 1
        # self.effWidth = self.width
        # self.effHeight = self.height
        # self.effHeight = 8

        # print('SetCrop Code:', windll.atmcd64d.SetIsolatedCropMode(1, 64, 512, 8, 1))
        # print('SetCrop Code:', windll.atmcd64d.SetIsolatedCropModeEx(1, 64, 496, 8, 1, 224, 8))
        # self.effHeight = int(self.height/64)
        # self.effWidth = 496

        readexposure = c_float()
        readaccumulate = c_float()
        readkinetic = c_float()
        readouttime = c_float()
        windll.atmcd64d.GetAcquisitionTimings(byref(readexposure), byref(readaccumulate), byref(readkinetic))
        print('ReadOut Code:', windll.atmcd64d.GetReadOutTime(byref(readouttime)))

        print('Andor read timings:')
        print('  read exposure time =', readexposure.value * 1000, 'ms')
        print('  read accumulate time =', readaccumulate.value * 1000, 'ms')
        print('  read kinetic time =', readkinetic.value * 1000, 'ms')
        print('  read readoutMax time =', readouttime.value * 1000, 'ms')
        print('Andor image size:', self.effWidth, 'x', self.effHeight)

        gainvalue = c_float()
        windll.atmcd64d.GetPreAmpGain(ampgain, byref(gainvalue))
        print('Andor preamp gain #%d' % ampgain, '=', gainvalue.value)
        windll.atmcd64d.SetPreAmpGain(ampgain)

        if emAdvMode == 1:print("EMAdvanced = On")
        else:print("EMAdvanced = Off")
        print('Andor EM gain = ', emGainUse, 'emAdvMode = ', emAdvMode)

        windll.atmcd64d.SetEMGainMode(3) # Real EM Gain

        valid=windll.atmcd64d.SetEMAdvanced(emAdvMode)  #0 for off, 1 for on
        if valid==20002:print("SetEMAdvanced ok")
        else: print("SetEMAdvanced error = ", valid)

        valid=windll.atmcd64d.SetEMCCDGain(emGainUse)  # accept values 0-300
        if valid==20002:print("SetEMCCDGain ok")
        else: print("SetEMCCDGain error = ", valid)

        valid=windll.atmcd64d.SetHighCapacity(highcapacity)  # accept values 0-300
        if valid==20002:print("SetHighCapacity ok")
        else: print("SetHighCapacity error = ", valid)





    def start_acquisition(self):
        acq=windll.atmcd64d.StartAcquisition()
        if acq==20002: print('Acquisition started successfully')
        else: print("Acqusition error = ",acq)
        self.numberandorimages = 0

    def get_status(self):
        numImg = c_long()
        windll.atmcd64d.GetTotalNumberImagesAcquired(byref(numImg))
        return str((windll.atmcd64d.GetStatus(),
                   numImg.value))

    def get_num_newImgs(self):
        startIdx = c_long()
        stopIdx = c_long()
        windll.atmcd64d.GetNumberNewImages(startIdx, stopIdx)
        value = stopIdx.value - startIdx.value
        return value

    def roidata(self):
        if self.effHeight <= 0 or self.effWidth <= 0:
            raise NoCamError()

        starttime = time.time()

        if self.andormode == 'Live' or self.andormode == 'AutoLoad':
            # print('Retrieving image: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            valid = windll.atmcd64d.GetMostRecentImage(img, c_long(self.effWidth * self.effHeight))
            if valid == 20024: raise CamTimeoutError
            # windll.atmcd64d.GetOldestImage(img, c_long(self.effWidth * self.effHeight))
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
        elif self.andormode == 'TriggeredAcquisition':
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            valid = windll.atmcd64d.GetOldestImage(img, c_long(self.effWidth * self.effHeight))
            if valid == 20024: raise CamTimeoutError
            # print('Retrieving image: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
        elif self.andormode == 'Detecter':
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            valid = windll.atmcd64d.GetOldestImage(img, c_long(self.effWidth * self.effHeight))
            if valid == 20024: raise CamTimeoutError
            # print('Retrieving image: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
        elif self.andormode == 'FastKinetics':
            # print('Retrieving images: ', self.effWidth, 'x', self.effHeight, self.andormode)
            imgtype = c_long * (self.effWidth * self.effHeight)
            img = imgtype()
            windll.atmcd64d.GetAcquiredData(img, c_long(self.effWidth * self.effHeight))
            imgout = numpy.ctypeslib.as_array(img)
            imgout = numpy.reshape(imgout, (self.effHeight, self.effWidth))
            windll.atmcd64d.StartAcquisition()

        endtime = time.time()
        # print('  readout time = ', endtime - starttime, ' s')
        if DEBUG_MODE: self.imgoutRandModifier_IonSim(imgout)
        return imgout

    def setSize(self, hBin, vBin, hStart, hEnd, vStart, vEnd):
        print('Changing size to {h} x {w} * {b}'.format(h=hEnd - hStart + 1, w=vEnd - vStart + 1, b=(hBin,vBin)))
        # Save settings
        self.hStart = hStart
        self.hEnd = hEnd
        self.vStart = vStart
        self.vEnd = vEnd

        # Compensate for "frame_width() == 0"
        if DEBUG_MODE:
            if not self.hEnd:
                self.hEnd = 512
                self.vEnd = 512


    def imgoutRandModifier(self, imgout):

        effHeight, effWidth = imgout.shape[0], imgout.shape[1]
        for i in range(effHeight):
            for j in range(effWidth):
                imgout[i][j] = imgout[i][j] + numpy.random.randint(0, 2) if self.hStart <= i+1 < self.hEnd and \
                                                                            self.vStart <= j+1 < self.vEnd else 0

                # if __name__ == '__main__':
                # cam = Cam()
                # cam.open()
                # cam.start_cooling()
                # print(cam.gettemperature())
                # time.sleep(5)
                # print(cam.gettemperature())
                # cam.wait()
                # img = cam.roidata()
                # print()
                # cam.close()

    # Simulates camera data more accurately -- brightness clustered around several 'ions'
    def imgoutRandModifier_IonSim(self, imgout):
        ionList = [(25, i) for i in range(10, 40, 5)]  # Sample ion chain, change as needed

        effHeight, effWidth = imgout.shape[0], imgout.shape[1]
        sampling = 10  # Higher sampling -> lower variances, smoother contrast

        # L_2 norm of 2 points
        def dist(u, v):
            return (numpy.abs(u[0] - v[0])**2 + numpy.abs(u[1] - v[1])**2)**0.5

        # inv prop to max dist from ions
        def prob(x, y):
            return 1/max(min([dist((x, y), ion) for ion in ionList]), 1)

        for i in range(effHeight):
            for j in range(effWidth):
                if self.hStart <= i + 1 < self.hEnd and self.vStart <= j + 1 < self.vEnd:
                    imgout[i][j] = numpy.random.binomial(sampling, prob(i, j))
                else:
                    imgout[i][j] = 0
