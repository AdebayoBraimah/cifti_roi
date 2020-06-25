# cifti_roi

Identifies clusters and the corresponding ROIs that overlap with each cluster. CIFTI clusters are identified first on the cortical (mesh) surface, and then secondly in the subcortical (volume) ROIs. Overlapping CIFTI clusters and ROIs are then written to a spreadsheet. Primarily intended for post-statistical analysis (e.g. PALM, and FEAT higher level analyses).

Requirements:
* Python v3.5+
	* Modules/Packages
		* numpy
		* nibabel
		* pandas
* FSL (FMRIB Software Library)
	* Required only if attempting to identify volumetric clusters and their overlapping ROIs

