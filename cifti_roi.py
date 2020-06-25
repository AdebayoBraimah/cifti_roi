#!/usr/bin/env python

'''Identifies clusters in CIFTI files, identifies their overlapping ROIs, and writes them out to a CSV file.'''

# Import modules
import os
import re
import sys
import numpy as np
import nibabel as nib
import pandas as pd
import subprocess
import platform

# Import third-party modules
import nifti_roi.nifti_roi as nro

# Import modules for argument parsing
import argparse

# Define class(es)

class Command():
    '''
    Creates a command and an empty command list for UNIX command line programs/applications. Primary use and
    use-cases are intended for the subprocess module and its associated classes (i.e. call/run).
    Attributes:
        command: Command to be performed on the command line
    '''

    def __init__(self):
        '''
        Init doc-string for Command class.
        '''
        pass

    def init_cmd(self, command):
        '''
        Init command function for initializing commands to be used on UNIX command line.
        
        Arguments:
            command (string): Command to be used. Note: command used must be in system path
        Returns:
            cmd_list (list): Mutable list that can be appended to.
        '''
        self.command = command
        self.cmd_list = [f"{self.command}"]
        return self.cmd_list

# Define functions

def run(cmd_list,stdout="",stderr=""):
    '''
    Uses python's built-in subprocess class to run a command from an input command list.
    The standard output and error can optionally be written to file.
    
    Arguments:
        cmd_list(list): Input command list to be run from the UNIX command line.
        stdout(file): Output file to write standard output to.
        stderr(file): Output file to write standard error to.
    Returns:
        stdout(file): Output file that contains the standard output.
        stderr(file): Output file that contains the standard error.
    '''
    if stdout and stderr:
        with open(stdout,"w") as file:
            with open(stderr,"w") as file_err:
                subprocess.call(cmd_list,stdout=file,stderr=file_err)
                file.close(); file_err.close()
    elif stdout:
        with open(stdout,"w") as file:
            subprocess.call(cmd_list,stdout=file)
            file.close()
        stderr = None
    else:
        subprocess.call(cmd_list)
        stdout = None
        stderr = None

    return stdout,stderr

def load_hemi_labels(file,wb_struct,map_number=1):
    '''
    Loads left or right hemisphere of CIFTI dlabel (dense label) file.
    
    Arguments:
        file(file): Input CIFTI dlabel file
        wb_struct(str): Structure - valid inputs are either: CORTEX_LEFT or CORTEX_RIGHT
        map_number(int): Map number of the input CIFTI dlabel map
    Returns:
        atlas_data(numpy array): Numpy array of labeled surface vertices for some specific hemisphere
        atlas_dict(dict): Dictionary of label IDs to ROI names
    '''
    
    gii_label = 'data.label.gii'
    
    load_label = Command().init_cmd("wb_command"); load_label.append("-cifti-separate")
    
    load_label.append(file)
    load_label.append("COLUMN")
    load_label.append("-label"); load_label.append(wb_struct)
    load_label.append(gii_label)
    
    run(load_label)
    
    gifti_img = nib.load(gii_label)
    
    atlas_data = gifti_img.get_arrays_from_intent('NIFTI_INTENT_LABEL')[map_number-1].data
    atlas_dict = gifti_img.get_labeltable().get_labels_as_dict()
    
    os.remove(gii_label)
    
    return atlas_data,atlas_dict

def load_gii_data(file,intent='NIFTI_INTENT_NORMAL'):
    '''
    Loads GIFTI surface/metric data (.func or .shape) and stores the 
    data as NxMxP numpy array - in which N = X dimensions, M = Y 
    dimensions, and P = the number of TRs or timepoints of the input 
    GIFTI data.
    
    Arguments:
        file(file): Input GIFTI surface/metric file
        intent(str): File read intention for nibabel i/o module
    Returns:
        data(numpy array): Numpy array of data for GIFTI file
    '''
    
    # Load surface data
    surf_dist_nib = nib.load(file)
    
    # Number of TRs in data
    num_da = surf_dist_nib.numDA
    
    # Read all arrays and concatenate temporally
    array1 = surf_dist_nib.get_arrays_from_intent(intent)[0]
    
    data = array1.data
    
    if num_da >= 1:
        for da in range(1,num_da):
            data = np.vstack((data,surf_dist_nib.get_arrays_from_intent(intent)[da].data))
            
    # Transpose data such that vertices are organized by TR
    data = np.transpose(data)
    
    # If output is 1D, make it 2D
    if len(data.shape) == 1:
        data = data.reshape(data.shape[0],1)
        
    return data

def load_hemi_data(file,wb_struct):
    '''
    Wrapper function for `load_gii_data`:
    Loads GIFTI surface/metric data (.func or .shape) and stores the 
    data as NxMxP numpy array - in which N = X dimensions, M = Y 
    dimensions, and P = the number of TRs or timepoints of the input 
    GIFTI data.
    
    Arguments:
        file(file): Input GIFTI surface/metric file
        wb_struct(str): Structure - valid inputs are either: CORTEX_LEFT or CORTEX_RIGHT
    Returns:
        data(numpy array): Numpy array of data for GIFTI file
    '''
    
    gii_data = 'data.func.gii'
    
    load_gii = Command().init_cmd("wb_command"); load_gii.append("-cifti-separate")
    
    load_gii.append(file)
    load_gii.append("COLUMN")
    load_gii.append("-metric"); load_gii.append(wb_struct)
    load_gii.append(gii_data)
    
    run(load_gii)
    
    data = load_gii_data(gii_data)
    
    os.remove(gii_data)
    
    return data

def get_roi_name(cluster_data,atlas_data,atlas_dict):
    '''
    Finds ROI names from overlapping clusters on the cortical surface via
    vertex matching.
    
    Arguments:
        cluster_data(numpy array): Input CIFTI dlabel file
        atlas_data(numpy array): Numpy array of labeled surface vertices for some specific hemisphere
        atlas_dict(dict): Dictionary of label IDs to ROI names
    Returns:
        roi_list(list): List of ROIs overlapped by cluster(s)
    '''
    
    # for idx,val in enumerate(cluster_data.astype(int)):
    for idx,val in enumerate(cluster_data):
        if cluster_data[idx] == 0:
            atlas_data[idx] = 0
    
    tmp_list = list()
    roi_list = list()
    
    for i in np.unique(atlas_data)[1:]:
        # print(atlas_dict[i])
        tmp_list = atlas_dict[i]
        roi_list.append(tmp_list)
    
    return roi_list

def find_clusters(file,left_surf,right_surf,thresh = 1.77,distance = 20):
    '''
    Loads left or right hemisphere of CIFTI dscalar (dense scalar) file and identifies clusters
    and returns a numpy array of the clusters' vertices.
    
    Arguments:
        file(file): Input CIFTI dscalar file
        left_surf(file): Left surface file (preferably midthickness file)
        right_surf(file): Rigth surface file (preferably midthickness file)
        thresh(float): Threshold values below this value
        distance(float): Minimum distance between two or more clusters
    Returns:
        cii_data(numpy array): Numpy array of surface vertices
    '''
    
    cii_data = 'clusters.dscalar.nii'
    
    thresh = str(thresh)
    distance = str(distance)
    
    find_cluster = Command().init_cmd("wb_command"); find_cluster.append("-cifti-find-clusters")
    find_cluster.append(file)
    find_cluster.append(thresh); find_cluster.append(distance)
    find_cluster.append(thresh); find_cluster.append(distance)
    find_cluster.append("COLUMN")
    find_cluster.append(cii_data)
    find_cluster.append("-left-surface")
    find_cluster.append(left_surf)
    find_cluster.append("-right-surface")
    find_cluster.append(right_surf)
    
    run(find_cluster)
    
    return cii_data

def write_spread(file,out_file,roi_list):
    '''
    Writes the contents or roi_list to a spreadsheet.
    
    Arguments:
        file (file): Input CIFTI file
        out_file (file): Output csv file name and path. This file need not exist at runtime.
        roi_list(list): List of ROIs to write to file
    Returns: 
        out_file (csv file): Output csv file name and path.
    '''
    
    # Strip csv file extension from output file name
    if '.csv' in out_file:
        out_file = os.path.splitext(out_file)[0]
        out_file = out_file + '.csv'
    elif '.tsv' in out_file:
        out_file = os.path.splitext(out_file)[0]
        out_file = out_file + '.csv'
    elif '.txt' in out_file:
        out_file = os.path.splitext(out_file)[0]
        out_file = out_file + '.csv'
    else:
        pass
    
    # Construct image dictionary
    file = os.path.abspath(file)
    img_dict = {"File":file,
         "ROIs":[roi_list]}
    
    # Create dataframe from image dictionary
    df = pd.DataFrame.from_dict(img_dict,orient='columns')
    
    # Write output CSV file
    if os.path.exists(out_file):
        df.to_csv(out_file, sep=",", header=False, index=False, mode='a')
    else:
        df.to_csv(out_file, sep=",", header=True, index=False, mode='w')
    
    return out_file

def proc_hemi(gii_data, gii_atlas, wb_struct):
    '''
    Wrapper function for `load_hemi_labels`, `load_hemi_data`, and `get_roi_name`:
    
    Loads GIFTI data to find the names or ROIs that overlap with clusters for some hemisphere
    
    Arguments:
        gii_data(file): Input GIFTI file
        gii_atlas(file): Input GIFTI atlas label file
        wb_struct(str): Structure - valid inputs are either: CORTEX_LEFT or CORTEX_RIGHT
    Returns:
        roi_list(list): List of ROIs that overlap with CIFTI cluster
    '''
       
    
    # Get atlas information
    [atlas_data,atlas_dict] = load_hemi_labels(gii_atlas,wb_struct)
    
    # Get cluster data
    cluster_data = load_hemi_data(gii_data, wb_struct)
    
    # Get ROI names from overlapping cluster(s)
    roi_list = get_roi_name(cluster_data,atlas_data,atlas_dict)
    
    return roi_list

def load_vol_data(file,thresh=1.77,dist=20,vol_atlas_num=4,nii_atlas = "",atlas_info = ""):
    '''
    Creates (subcortical) NIFTI volumetric data from input CIFTI, followed by identifying the ROIs that
    are overlapped by clusters.
    
    Arguments:
        file(file): Input CIFTI file
        thresh(float): Cluster minimum threshold
        dist(float): Minimum distance between clusters
        vol_atlas_num(int): Atlas to be used in FSL's `atlasquery`. Number corresponds to an atlas. See FSL's `atlasquery` help menu for details.
        nii_atlas(NIFTI file): NIFTI atlas file
        atlas_info(file): Corresponding CSV key, value pairs of ROIs for atlas file
    Returns:
        roi_list(list): List of ROIs that overlap with some given cluster
    '''
    
    vol_data = 'data.nii.gz'
    
    load_vol = Command().init_cmd("wb_command"); load_vol.append("-cifti-separate")
    
    load_vol.append(file)
    load_vol.append("COLUMN")
    load_vol.append("-volume-all")
    load_vol.append(vol_data)
    
    run(load_vol)
    
    if nii_atlas and atlas_info:
        # Read atlas data and info
        [atlas_data,atlas_dict] = nro.load_atlas_data(nii_atlas,atlas_info)

        # Read NIFTI data and find clusters
        img_data = nro.load_nii_vol(vol_data,thresh,dist)

        # Identify cluster and ROI overlaps
        roi_list = nro.get_roi_name(img_data,atlas_data,atlas_dict)
    else:
        roi_list = nro.vol_clust(vol_data,thresh,dist,vol_atlas_num)
    
    os.remove(vol_data)
    
    return roi_list

def proc_stat_cluster(cii_file,cii_atlas,out_file,left_surf,right_surf,thresh=1.77,distance=20,vol_atlas_num=4,nii_atlas = "",atlas_info = ""):
    '''
    Identifies ROIs that have overlap with some cluster(s) from the input CIFTI file.
    
    Arguments:
        cii_file(file): Input CIFTI dscalar file
        cii_atlas(file): Input CIFTI dlabel (atlas) file
        out_file(file): Name for output CSV file
        left_surf(file): Left surface file (preferably midthickness file)
        right_surf(file): Rigth surface file (preferably midthickness file)
        thresh(float): Threshold values below this value
        distance(float): Minimum distance between two or more clusters
        vol_atlas_num(int): Atlas to be used in FSL's `atlasquery`. Number corresponds to an atlas. See FSL's `atlasquery` help menu for details.
        nii_atlas(NIFTI file): NIFTI atlas file
        atlas_info(file): Corresponding CSV key, value pairs of ROIs for atlas file
    Returns:
        out_file(file): Output CSV file
    '''
    
    # Isolate cluster data
    cii_data = find_clusters(cii_file,left_surf,right_surf,thresh,distance)
    
    # Significant cluster overlap ROI list
    roi_list = list()
    tmp_list = list()
    
    # Iterate through wb_structures
    wb_structs = ["CORTEX_LEFT","CORTEX_RIGHT"]
    
    for wb_struct in wb_structs:
        tmp_list = proc_hemi(cii_data,cii_atlas,wb_struct)
        if len(tmp_list) == 0:
            pass
        else:
            roi_list.extend(tmp_list)
    
    os.remove(cii_data)
    
    if platform.system().lower() != 'windows':
        tmp_list = load_vol_data(cii_file,thresh,distance,vol_atlas_num,nii_atlas,atlas_info)
    
    if len(tmp_list) == 0:
        pass
    else:
        roi_list.extend(tmp_list)
    
    # Write output spreadsheet of ROIs
    if len(roi_list) != 0:
        out_file = write_spread(cii_file,out_file,roi_list)
        
    return out_file

if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(description="Finds cifti surface clusters and writes the overlapping ROIs to a CSV file. \n\
\n\
NIFTI volume clusters are handled in a different manner, utilizing one of two methods that must be specified: \n\
\n\
1. A NIFTI volume file is provided, along with an atlas number to determine which ROI the cluster overlaps (this requires the input NIFTI volume to be in MNI space).\n\
2. A NIFTI volume file is provided, along with a separate atlas NIFTI volume and an enumrated CSV file, that contains the ROI intensity values as a number-ROI pair (this requires the input NIFTI volume to be in this atlas' space.) \n\
\n\
For a list of available atlases, see the '--dump-vol-atlases' option for details.\n\
\n\
Note: \n\
- Enumrated CSV files must not contain Window's carriage returns. \n\
- Input template left and right surfaces should match the input CIFTI file.",
# usage="use '%(prog)s --help' for more information",
formatter_class=argparse.RawTextHelpFormatter)

    # Parse Arguments
    # Required Arguments
    reqoptions = parser.add_argument_group('Required arguments')
    reqoptions.add_argument('-i', '-in', '--input',
                            type=str,
                            dest="cii_file",
                            metavar="STATS.dscalar.nii",
                            required=False,
                            help="Cifti image file.")
    reqoptions.add_argument('-o', '-out', '--output',
                            type=str,
                            dest="out_file",
                            metavar="OUTPUT.csv",
                            required=False,
                            help="Output spreadsheet name.")
    reqoptions.add_argument('-l', '-left', '--left-surface',
                            type=str,
                            dest="left_gii",
                            metavar="GII",
                            required=False,
                            help="Input left gifti surface.")
    reqoptions.add_argument('-r', '-right', '--right-surface',
                            type=str,
                            dest="right_gii",
                            metavar="GII",
                            required=False,
                            help="Input right gifti surface.")
    reqoptions.add_argument('-c','--cii-atlas',
                            type=str,
                            dest="cii_atlas",
                            metavar="ATLAS.dlabel.nii",
                            required=False,
                            help="Cifti atlas file.")

     # Atlasquery options
    atlqoptions = parser.add_argument_group('Volumetric atlasquery options')
    atlqoptions.add_argument('--vol-atlas-num',
                            type=int,
                            dest="vol_atlas_num",
                            metavar="INT",
                            required=False,
                            help="Atlas number. See '--dump-vol-atlases' for details.")

    # Stand-alone atlas options
    atlsoptions = parser.add_argument_group('Stand-alone volumetric atlas options')
    atlsoptions.add_argument('--vol-atlas',
                            type=str,
                            dest="vol_atlas",
                            metavar="ATLAS.nii.gz",
                            required=False,
                            help="NIFTI atlas file.")
    atlsoptions.add_argument('--atlas-info',
                            type=str,
                            dest="vol_info",
                            metavar="ATLAS.info.csv",
                            required=False,
                            help="Atlas information file.")

    # Optional Arguments
    optoptions = parser.add_argument_group('Optional arguments')
    optoptions.add_argument('-t', '-thresh', '--thresh',
                            type=float,
                            dest="thresh",
                            metavar="FLOAT",
                            default=1.77,
                            required=False,
                            help="Cluster threshold. [default: 1.77]")
    optoptions.add_argument('-d', '-dist', '--distance',
                            type=float,
                            dest="dist",
                            metavar="FLOAT",
                            default=20,
                            required=False,
                            help="Minimum distance between clusters. [default: 20]")
    optoptions.add_argument('--dump-vol-atlases',
                            dest="dump_vol_atlases",
                            required=False,
                            action="store_true",
                            help="Prints available volumetric atlases and their corresponding atlas number.")

    args = parser.parse_args()

    # Print help message in the case
    # of no arguments
    try:
        args = parser.parse_args()
    except SystemExit as err:
        if err.code == 2:
            parser.print_help()

    # Run
    if args.dump_vol_atlases:
        # Check if volumetric atlases need to be printed to screen
        nro.print_atlases()
    elif args.cii_file and args.out_file and args.left_gii and args.right_gii and args.cii_atlas:
        # Check if required arguments were passed to the command line
        if args.vol_atlas and args.vol_info:
            # Check if stand-alone volumetric atlas files and info were passed as arguments
            args.out_file = proc_stat_cluster(cii_file=args.cii_file,cii_atlas=args.cii_atlas,out_file=args.out_file,left_surf=args.left_gii,right_surf=args.right_gii,thresh=args.thresh,distance=args.dist,nii_atlas=args.vol_atlas,atlas_info=args.vol_info)
        elif args.vol_atlas_num:
            # Check if volumetric atlas query number was passed as argument
            args.out_file = proc_stat_cluster(cii_file=args.cii_file,cii_atlas=args.cii_atlas,out_file=args.out_file,left_surf=args.left_gii,right_surf=args.right_gii,thresh=args.thresh,distance=args.dist,vol_atlas_num=args.vol_atlas_num)    
    else:
        print("")
        print("Not all valid options were specified. Please see help menu for details.")
        print("")
        sys.exit(1)
