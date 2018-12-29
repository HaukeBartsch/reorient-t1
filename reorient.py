#!/usr/bin/env python3

import os
import pydicom as dicom
import json
import numpy
import copy
import matplotlib.pyplot as plt
from matplotlib import pyplot, cm
from pydicom.uid import generate_uid

filepath = '/home/abcdproj1/data/DAL_ABCD_HPT/raw/MRIRAW_S022_PhantomTravelingHuman001CUB_20181026_154138_20181026.154138.247000_1/st001_ser0005/'

lstFilesDCM = []  # create an empty list
for dirName, subdirList, fileList in os.walk(filepath):
    for filename in fileList:
        if ".dcm" in filename.lower():  # check whether the file's DICOM
            lstFilesDCM.append(os.path.join(dirName,filename))


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
#slices = []
for filenameDCM in lstFilesDCM:
    # read the file
    ds = dicom.read_file(filenameDCM)
    #slices.append(ds)
    # store the raw image data
    ArrayDicom[:, :, lstFilesDCM.index(filenameDCM)] = ds.pixel_array

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
print(ArrayDICOM2.shape)
print(RefDs.ImageOrientationPatient)


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
    fname_out = "/tmp/%s_im%3.4i.dcm" % ("output1", slice)  # sprintf('%s/%s_im%3.4i.dcm',output,inputname, i)
    print("write slice %d as %s" % (slice, fname_out))
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
    fname_out = "/tmp/%s_im%3.4i.dcm" % ("output2", slice)  # sprintf('%s/%s_im%3.4i.dcm',output,inputname, i)
    print("write slice %d as %s" % (slice, fname_out))
    # print('%s - Writing DICOM images, %d of %d\r',fname_out,slice,  numpy.shape(ArrayDICOM2)[2])
    # dicomwrite(int16(dat(:,:,i)'), fname_out, metadata, 'CreateMode', 'copy')
    metadata.PixelData = ArrayDICOM3[:,:,slice].tobytes()
    # we get an error message if we try to save as is. We have to delete these fields every single time
    del metadata[(0x0002,0x0000):(0x0003,0x0000)]
    dicom.filewriter.write_file(fname_out, metadata, write_like_original=True)
