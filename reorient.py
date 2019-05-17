#!/usr/bin/env python3

#
# Assumptions:
#    - the input directory contains a single series of sagittal images
# Based on Hauke's reorient.py
#
#Created by Feng Xue 05/15/2019

import os
import pydicom as dicom
#import json
import sys, getopt
import numpy
import copy
#import matplotlib.pyplot as plt
#from matplotlib import pyplot, cm
from pydicom.uid import generate_uid




def main(argv):
    filepath  = ''
    outputdir = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["idir=","odir="])
    except getopt.GetoptError:
        print('reorient.py -i <input directory> -o <output directory>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
           print('reorient.py -i <input directory> -o <output directory>')
           sys.exit()
        elif opt in ("-i", "--idir"):
           filepath = arg
        elif opt in ("-o", "--odir"):
           outputdir = arg
    #print('Input directory is \"%s\"' % filepath)
    #print('Output directory is \"%s\"' % outputdir)

    if filepath == '':
        filepath = '/home/abcdproj1/data/DAL_ABCD_HPT/raw/MRIRAW_S022_PhantomTravelingHuman001CUB_20181026_154138_20181026.154138.247000_1/st001_ser0005/'

    if outputdir == '':
        print("Error: provide -o outputdir")
        sys.exit(-1)

    print("Reorienting DICOM files")
    print("Info: Try to find input DICOM files in %s" % filepath)

    lstFilesDCM = numpy.array([])  # create an empty list
    InstanceNumbers = numpy.array([])
    for dirName, subdirList, fileList in os.walk(filepath):
        for filename in fileList:
            try:
                ds = dicom.read_file(os.path.join(dirName,filename),stop_before_pixels=True)
                if "EchoTime" in ds and "InstanceNumber" in ds:
                    if ds.InstanceNumber in InstanceNumbers:
                        raise Exception("Error: Duplicated InstanceNumber found: %d" % ds.InstanceNumber)
                    else:
                        lstFilesDCM = numpy.append(lstFilesDCM,os.path.join(dirName,filename))
                        InstanceNumbers = numpy.append(InstanceNumbers,ds.InstanceNumber)
                else:
                    print('%s is not a valid DICOM file' % filename)
            except TypeError:
                print('%s is not a DICOM file' % filename)
            except Exception as inst:
                print(inst)
                sys.exit(-1)
    idx = numpy.argsort(InstanceNumbers)
    lstFilesDCM = lstFilesDCM[idx]
    InstanceNumbers = []
    idx = []

    RefDs = dicom.read_file(lstFilesDCM[int(len(lstFilesDCM)/2)])

    # Load dimensions based on the number of rows, columns, and slices (along the Z axis)
    ConstPixelDims = (int(RefDs.Rows), int(RefDs.Columns), len(lstFilesDCM))

    # Load spacing values (in mm)
    ConstPixelSpacing = (float(RefDs.PixelSpacing[0]), float(RefDs.PixelSpacing[1]), float(RefDs.SliceThickness))

    x = numpy.arange(0.0, (ConstPixelDims[0]+1)*ConstPixelSpacing[0], ConstPixelSpacing[0])
    y = numpy.arange(0.0, (ConstPixelDims[1]+1)*ConstPixelSpacing[1], ConstPixelSpacing[1])
    z = numpy.arange(0.0, (ConstPixelDims[2]+1)*ConstPixelSpacing[2], ConstPixelSpacing[2])


    # The array is sized based on 'ConstPixelDims'
    ArrayDicom  = numpy.zeros(ConstPixelDims, dtype=RefDs.pixel_array.dtype)

    # loop through all the DICOM files
    # TODO: we should go through here twice, first time read in all the slices
    #       next time we sort the slices (by slice location for example) and
    #       import them into the volume
    #slices = []
    idx=0
    for filenameDCM in lstFilesDCM:
        # read the file
        ds = dicom.read_file(filenameDCM)
        #slices.append(ds)
        # store the raw image data
        #ArrayDicom[:, :, lstFilesDCM.index(filenameDCM)] = ds.pixel_array
        ArrayDicom[:, :, idx] = ds.pixel_array
        idx += 1

    print("reading done...")
    #pyplot.figure(dpi=300)
    #pyplot.axes().set_aspect('equal', 'datalim')
    #pyplot.set_cmap(pyplot.gray())
    #pyplot.pcolormesh(x, y, numpy.flipud(ArrayDicom[:, :, 80]))
    # plt.show(block=True)

    # now we can reorient the volume and write the file out again
    # ArrayDICOM2 = ArrayDicom[:,:,::-1]
    tmp = ArrayDicom.copy()
    ArrayDICOM2 = numpy.transpose(tmp, (0, 2, 1))
    #print(ArrayDICOM2.shape)
    #print(RefDs.ImageOrientationPatient)


    # write out 
    metadata = copy.deepcopy( RefDs )
    SeriesInstanceUID = generate_uid()
    FrameOfReferenceUID = generate_uid()
    metadata.FrameOfReferenceUID = FrameOfReferenceUID
    SeriesNumber = metadata.SeriesNumber + 1000
    pixelspacing = [ int(ConstPixelSpacing[1]), int(ConstPixelSpacing[2]) ]
    # metadata.TransferSyntaxUID = dicom.uid.ExplicitVRLittleEndian
    SeriesDescription = "%s - reformat" % RefDs.SeriesDescription
    StudyDescription = RefDs.StudyDescription

    for slice in range(numpy.shape(ArrayDICOM2)[2]):
        metadata.Rows = ConstPixelDims[0]
        metadata.Columns = ConstPixelDims[2]
        # these need to be unique for this image
        metadata.SOPInstanceUID = generate_uid()
        #metadata.LargestImagePixelValue  = 32768
        #metadata.SmallestImagePixelValue = 0
        metadata.BitsAllocated = 16
        metadata.BitsStored    = 16
        metadata.HighBit       = 15
        metadata.BitDepth      = 16
        metadata.InstanceNumber = slice
        #metadata.PatientID    = PatientID;
        #metadata.RescaleSlope = RefDs.RescaleSlope
        #metadata.RescaleIntercept = RefDs.RescaleIntercept
        metadata.WindowWidth  = RefDs.WindowWidth 
        metadata.WindowCenter = RefDs.WindowCenter
        #metadata.ProtocolName = 'MRI'
        metadata.Modality     = 'MR'
        metadata.ImageType    = [ "ORIGINAL", "PRIMARY", "3D" ]
        #metadata.PatientName  = PatientID;
        #metadata.PatientID    = PatientID;
        metadata.SeriesDescription = SeriesDescription
        metadata.StudyDescription  = StudyDescription
        metadata.SeriesNumber      = SeriesNumber
        metadata.SeriesInstanceUID = SeriesInstanceUID
        metadata.InstitutionName   = 'redicom at CMIG'
        metadata.StationName       = ''
        metadata.PixelSpacing      = pixelspacing
        metadata.SliceLocation     = (float(RefDs.SliceThickness)*slice) # sprintf('%f', data.hdr.dime.pixdim(4)*i);
        metadata.SliceThickness    = float(RefDs.SliceThickness)
        metadata.ImagePositionPatient = [ 0, float(RefDs.SliceThickness)*slice, 0 ]  # sprintf('%f\\%f\\%f', 0, 0, data.hdr.dime.pixdim(4)*i)
        #print(metadata.ImageOrientationPatient)
        metadata.ImageOrientationPatient = [ 1, 0, 0, -0, 0, -1 ]
        metadata.SpacingBetweenSlices = float(RefDs.SliceThickness) # data.hdr.dime.pixdim(4)
        metadata.ImagesInSeries = numpy.shape(ArrayDICOM2)[2] # data.hdr.dime.dim(4)
        metadata.ManufacturerModelName = 'fake SIEMENS'
        metadata.SOPClassUID       = '1.2.840.10008.5.1.4.1.1.4' # MRI image storage
        metadata.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
        fname_out = "/%s/%s_im%3.4i.dcm" % (outputdir, "output1", slice)  # sprintf('%s/%s_im%3.4i.dcm',output,inputname, i)
        #print("write slice %d as %s" % (slice, fname_out))
        # print('%s - Writing DICOM images, %d of %d\r',fname_out,slice,  numpy.shape(ArrayDICOM2)[2])
        # dicomwrite(int16(dat(:,:,i)'), fname_out, metadata, 'CreateMode', 'copy')
        metadata.PixelData = ArrayDICOM2[:,:,slice].tobytes()
        # metadata.save_as(fname_out)
        del metadata[(0x0002,0x0000):(0x0003,0x0000)]
        dicom.filewriter.write_file(fname_out, metadata, write_like_original=True)


    # ArrayDICOM3 = ArrayDicom[:,:,::-1]
    ArrayDICOM3 = numpy.transpose(numpy.copy(ArrayDicom), (1, 2, 0))

    # write out 
    metadata = copy.deepcopy( RefDs )
    SeriesInstanceUID = generate_uid()
    SeriesNumber = metadata.SeriesNumber + 1001
    #pixelspacing = [ ConstPixelDims[1], ConstPixelDims[2] ]
    pixelspacing = [ int(ConstPixelSpacing[1]), int(ConstPixelSpacing[2]) ]
    # metadata.TransferSyntaxUID = dicom.uid.ExplicitVRLittleEndian
    SeriesDescription = "%s - reformat" % RefDs.SeriesDescription
    StudyDescription = RefDs.StudyDescription

    for slice in range(numpy.shape(ArrayDICOM3)[2]):
        metadata.Rows = ConstPixelDims[1]
        metadata.Columns = ConstPixelDims[2]
        metadata.SOPInstanceUID = generate_uid()
        #metadata.LargestImagePixelValue  = 32768
        #metadata.SmallestImagePixelValue = 0
        metadata.BitsAllocated = 16
        metadata.BitsStored    = 16
        metadata.HighBit       = 15
        metadata.BitDepth      = 16
        metadata.InstanceNumber = slice
        #metadata.PatientID    = PatientID;
        #metadata.RescaleSlope = RefDs.RescaleSlope
        #metadata.RescaleIntercept = RefDs.RescaleIntercept
        metadata.WindowWidth  = RefDs.WindowWidth 
        metadata.WindowCenter = RefDs.WindowCenter
        #metadata.ProtocolName = 'MRI'
        metadata.Modality     = 'MR'
        metadata.ImageType    = [ "ORIGINAL", "PRIMARY", "3D" ]
        #metadata.PatientName  = PatientID;
        #metadata.PatientID    = PatientID;
        metadata.SeriesDescription = SeriesDescription
        metadata.StudyDescription  = StudyDescription
        metadata.SeriesNumber      = SeriesNumber
        metadata.SeriesInstanceUID = SeriesInstanceUID
        metadata.InstitutionName   = 'redicom at CMIG'
        metadata.StationName       = ''
        metadata.PixelSpacing      = pixelspacing
        metadata.SliceLocation     = (float(RefDs.SliceThickness)*slice) # sprintf('%f', data.hdr.dime.pixdim(4)*i);
        metadata.SliceThickness    = float(RefDs.SliceThickness)
        metadata.ImagePositionPatient = [ 0, 0, float(RefDs.SliceThickness)*slice ]  # sprintf('%f\\%f\\%f', 0, 0, data.hdr.dime.pixdim(4)*i)
        #print(metadata.ImageOrientationPatient)
        metadata.ImageOrientationPatient = [ 1, 0, 0, -0, 1, -0 ]
        metadata.SpacingBetweenSlices = float(RefDs.SliceThickness) # data.hdr.dime.pixdim(4)
        metadata.ImagesInSeries = numpy.shape(ArrayDICOM3)[2] # data.hdr.dime.dim(4)
        metadata.ManufacturerModelName = 'fake SIEMENS'
        metadata.SOPClassUID       = '1.2.840.10008.5.1.4.1.1.4' # MRI image storage
        metadata.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
        fname_out = "/%s/%s_im%3.4i.dcm" % (outputdir, "output2", slice)  # sprintf('%s/%s_im%3.4i.dcm',output,inputname, i)
        #print("write slice %d as %s" % (slice, fname_out))
        # print('%s - Writing DICOM images, %d of %d\r',fname_out,slice,  numpy.shape(ArrayDICOM2)[2])
        # dicomwrite(int16(dat(:,:,i)'), fname_out, metadata, 'CreateMode', 'copy')
        metadata.PixelData = ArrayDICOM3[:,:,slice].tobytes()
        # we get an error message if we try to save as is. We have to delete these fields every single time
        del metadata[(0x0002,0x0000):(0x0003,0x0000)]
        dicom.filewriter.write_file(fname_out, metadata, write_like_original=True)

    print('reoriented DICOM files were saved in: \"%s\"' % outputdir)


if __name__ == "__main__":
   main(sys.argv[1:])
