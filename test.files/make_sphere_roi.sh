#!/usr/bin/env bash

echo ""
echo "Input image: ${1}"
echo "ROI coordinates: ${2} ${3} ${4}"
echo "ROI size: ${5}"
echo ""
echo ""

p=$(pwd)
fslmaths ${1} -roi ${2} 1 ${3} 1 ${4} 1 0 1 ${p}/tmp_point_mask
fslmaths ${p}/tmp_point_mask -kernel sphere ${5} -fmean -bin ${p}/mask_sphere_${2}-${3}-${4} -odt float
rm ${p}/tmp_point_mask.*
