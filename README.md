# cifti_stats_ROI_overlap

Identifies clusters and the corresponding ROIs that overlap with each cluster. CIFTI clusters are identified first on the cortical (mesh) surface, and then secondly in the subcortical (volume) ROIs. Overlapping CIFTI clusters and ROIs are then written to a spreadsheet. Primarily intended for post-statistical analysis (e.g. PALM, and FEAT higher level analyses).

Requirements:
* Python v3.5+
	* Modules/Packages
		* numpy
		* nibabel
		* pandas
* FSL (FMRIB Software Library)
	* Required only if attempting to identify volumetric clusters and their overlapping ROIs


```

usage: cifti_stats_roi.py [-h] -i STATS.dscalar.nii -o OUTPUT.csv -l GII -r
                          GII -a ATLAS.dlabel.nii [-t FLOAT] [-d FLOAT]

Finds cifti surface clusters and writes the overlapping ROIs to a CSV file.

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
  -a ATLAS.dlabel.nii, -atlas ATLAS.dlabel.nii, --atlas ATLAS.dlabel.nii
                        Cifti atlas file.

Optional arguments:
  -t FLOAT, -thresh FLOAT, --thresh FLOAT
                        Cluster threshold.
  -d FLOAT, -dist FLOAT, --distance FLOAT
                        Minimum distance between clusters.

```

