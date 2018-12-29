# Test if we can re-orient a T1 image series in pydicom fast

Read in a DICOM series, reorient and write out again. This assumes that the input data is of a specific type - sagittal T1 MRI.

## Find some T1

```
grep "MPR" /home/abcdproj1/data/DAL_ABCD_HPT/raw/*/SeriesInfo.csv | grep -v LOCALIZER | grep -v JUNK | grep -v Nav_setter | awk -F"," '{ print $1$2 }'
```

Here an example:
```
 /home/abcdproj1/data/DAL_ABCD_HPT/raw/MRIRAW_S022_PhantomTravelingHuman001CUB_20181026_154138_20181026.154138.247000_1/st001_ser0005/
```

## Send to AMBRA

AETitle: DG_HARVESTER

```
/usr/bin/echoscu -v -aet DG_HARVESTER 172.19.172.30 4006

/usr/bin/storescu -v -aet DG_HARVESTER -aec TESTNODE +sd +r 172.19.172.30 4006 /tmp/*.dcm
```

Initial tests show that a T1 with 176 slices can be processed (read, re-orient and write) in 3 seconds.
