#!/usr/bin/env bash

#
# Command usage
#==============================================================================

Usage() {
  cat << USAGE

  Usage: $(basename ${0}) --coord "X,Y,Z"

Runs FSL's atlasquery for the \"Harvard-Oxford Subcortical Structural Atlas\" given some set of MNI space coordinates (in mm).

Required arguements:

-c,-coord,--coord     MNI space X,Y,Z coordinates (provided as quoted comma separated list)

USAGE
  exit 1
}

#
# Parse command line
#==============================================================================

# Parse options
while [[ ${#} -gt 0 ]]; do
  case "${1}" in
    -c|-coord|--coord) shift; coord=${1} ;;
    -h|-help|--help) Usage; ;;
    -*) echo "$(basename ${0}): Unrecognized option ${1}" >&2; Usage; ;;
    *) break ;;
  esac
  shift
done

#
# Perform atlas query
#==============================================================================

atlasquery --coord=${coord} --atlas="Harvard-Oxford Subcortical Structural Atlas"
