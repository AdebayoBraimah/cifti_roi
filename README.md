# cifti_roi

Identifies clusters and the corresponding ROIs that overlap with each cluster. CIFTI clusters are identified first on the cortical (mesh) surface, and then secondly in the subcortical (volume) ROIs. Overlapping CIFTI clusters and ROIs are then written to a spreadsheet. Primarily intended for post-statistical analysis (e.g. PALM, and FEAT higher level analyses).

Requirements:
* `Python` v3.5+
	* Modules/Packages
		* `numpy`
		* `nibabel`
		* `pandas`
* Connectome Workbench v1.3.2+
* `FSL` (FMRIB Software Library) v6.0+
	* Required only if attempting to identify volumetric clusters and their overlapping ROIs

```
usage: cifti_roi.py [-h] [-i STATS.dscalar.nii] [-o OUTPUT.csv] [-l GII]
                    [-r GII] [-c ATLAS.dlabel.nii] [--vol-atlas-num INT]
                    [--vol-atlas ATLAS.nii.gz] [--atlas-info ATLAS.info.csv]
                    [-t FLOAT] [-d FLOAT] [--dump-vol-atlases]

Finds cifti surface clusters and writes the overlapping ROIs to a CSV file. 

NIFTI volume clusters are handled in a different manner, utilizing one of two methods that must be specified: 

1. A NIFTI volume file is provided, along with an atlas number to determine which ROI the cluster overlaps (this requires the input NIFTI volume to be in MNI space).
2. A NIFTI volume file is provided, along with a separate atlas NIFTI volume and an enumrated CSV file, that contains the ROI intensity values as a number-ROI pair (this requires the input NIFTI volume to be in this atlas' space.) 

For a list of available atlases, see the '--dump-vol-atlases' option for details.

Note: 
- Enumrated CSV files must not contain Window's carriage returns. 
- Input template left and right surfaces should match the input CIFTI file.

optional arguments:
  -h, --help            show this help message and exit

Required arguments:
  -i STATS.dscalar.nii, -in STATS.dscalar.nii, --input STATS.dscalar.nii
                        Cifti image file.
  -o OUTPUT.csv, -out OUTPUT.csv, --output OUTPUT.csv
                        Output spreadsheet name.
  -l GII, -left GII, --left-surface GII
                        Input left gifti surface.
  -r GII, -right GII, --right-surface GII
                        Input right gifti surface.
  -c ATLAS.dlabel.nii, --cii-atlas ATLAS.dlabel.nii
                        Cifti atlas file.

Volumetric atlasquery options:
  --vol-atlas-num INT   Atlas number. See '--dump-vol-atlases' for details.

Stand-alone volumetric atlas options:
  --vol-atlas ATLAS.nii.gz
                        NIFTI atlas file.
  --atlas-info ATLAS.info.csv
                        Atlas information file.

Optional arguments:
  -t FLOAT, -thresh FLOAT, --thresh FLOAT
                        Cluster threshold. [default: 1.77]
  -d FLOAT, -dist FLOAT, --distance FLOAT
                        Minimum distance between clusters. [default: 20]
  --dump-vol-atlases    Prints available volumetric atlases and their corresponding atlas number.
```
