#!/usr/bin/env python

import os

import unittest
import lsst.utils.tests as tests

import eups
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.ip.isr as ipIsr
import numpy
import lsst.afw.display.ds9 as ds9

class IsrSdqaTestCases(unittest.TestCase):
    def setUp(self):
        darr = []
        mi = afwImage.MaskedImageF(10,10)
        mi.set(110, 0x0, 1)
        self.bbox = afwImage.BBox(afwImage.PointI(0,0), 1, 10)
        self.dbox = afwImage.BBox(afwImage.PointI(1,0), 9, 10)
        mask = afwImage.MaskU(mi.getMask(), self.dbox)
        satmask = afwImage.MaskU(mask.getDimensions(),0x0)
        badmask = afwImage.MaskU(mask.getDimensions(),0x0)
        satbmask = mask.getPlaneBitMask('SAT')
        badbmask = mask.getPlaneBitMask('BAD')
        img = afwImage.ImageF(mi.getImage(), self.dbox)
        oscan = afwImage.ImageF(mi.getImage(), self.bbox)
        for i in range(img.getWidth()):
            for j in range(img.getHeight()):
                img.set(i,j,i*img.getWidth() + j)
                darr.append(i*img.getWidth() + j)
        for i in range(oscan.getWidth()):
            for j in range(oscan.getHeight()):
                oscan.set(i,j,100)
        for i in range(10):
            satmask.set(int(i*satmask.getWidth()/10.), int(i*satmask.getHeight()/10.), satbmask)
            badmask.set(badmask.getWidth() - 1 - int(i*badmask.getWidth()/10.),
                    badmask.getHeight() - 1 - int(i*badmask.getHeight()/10.), badbmask)
        mask |= satmask
        mask |= badmask
        img2 = mi.getImage()
        self.mi = mi
        self.darr = numpy.asarray(darr)

    def tearDown(self):
        del self.mi
        del self.bbox
        del self.dbox

    def testAmpSdqa(self):
        exposure = afwImage.ExposureF(self.mi)
        ipIsr.calculateSdqaAmpRatings(exposure, self.bbox, self.dbox)
        metadata = exposure.getMetadata()
        self.assertEqual(metadata.get('overscanMin'), 100.)
        self.assertEqual(metadata.get('overscanMedian'), 100.)
        self.assertEqual(metadata.get('overscanMean'), 100.)
        self.assertEqual(metadata.get('overscanMax'), 100.)
        self.assertEqual(metadata.get('overscanStdDev'), 0.)
        self.assertEqual(metadata.get('nSaturatePix'), 10)

    def testCcdSdqa(self):
        nsat = 0
        exposure = afwImage.ExposureF(afwImage.MaskedImageF(self.mi, self.dbox))
        im = exposure.getMaskedImage().getImage()
        ipIsr.calculateSdqaCcdRatings(exposure)
        metadata = exposure.getMetadata()
        self.assertEqual(metadata.get('imageClipMean4Sig3Pass'), 40.5)
        self.assertEqual(metadata.get('imageMedian'), 40.5)
        #Since values 0 and 1 are masked min is 2.
        self.assertEqual(metadata.get('imageMin'), 2.)
        self.assertAlmostEqual(metadata.get('imageSigma'), 22.93223, 5)
        #Same here 80 and 81 are masked so max is 79
        self.assertEqual(metadata.get('imageMax'), 79.0)
        self.assertEqual(metadata.get('nSaturatePix'), 10)
        self.assertEqual(metadata.get('nBadCalibPix'), 10)

def suite():
    """Returns a suite containing all the test cases in this module."""
    tests.init()

    suites = []
    suites += unittest.makeSuite(IsrSdqaTestCases)
    suites += unittest.makeSuite(tests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(exit=False):
    """Run the tests"""
    tests.run(suite(), exit)

if __name__ == "__main__":
    run(True)