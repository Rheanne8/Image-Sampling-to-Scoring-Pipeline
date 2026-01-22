#!/bin/bash

###############################################################################
# SLURM Batch Script for Image Sampling Pipeline
#
# BEFORE RUNNING ON YOUR CLUSTER, CHANGE THE FOLLOWING:
#   1. Line 14: --partition=<YOUR_PARTITION>  (check with: sinfo)
#   2. Line 15: --qos=<YOUR_QOS>              (check with: sacctmgr show qos)
#   3. Line 16: --gres=gpu:1                  (remove if no GPU needed)
#   4. Line 42: source activate <YOUR_ENV>    (check with: conda info --envs)
#   5. Edit sample_perspectives.py: update DEFAULT_INPUT_DIR and DEFAULT_OUTPUT_DIR
#
# Submit with: sbatch run_sampling.sh
###############################################################################

### >>>>> CHANGE THIS: Your cluster's partition name <<<<<
#SBATCH --partition=UGGPU-TC1
#SBATCH --qos=normal
#SBATCH --gres=gpu:1

### Specify Memory allocate to this job ###
#SBATCH --mem=10G

### Specify number of core (CPU) to allocate to per node ###
#SBATCH --ntasks-per-node=1

### Specify number of node to compute ###
#SBATCH --nodes=1

### Optional: Specify node to execute the job ###
### Remove 1st # at next line for the option to take effect ###
##SBATCH --nodelist=TC1N07

### Specify Time Limit (in minutes) ###
#SBATCH --time=360

### Specify name for the job, filename format for output and error ###
#SBATCH --job-name=SamplingJob
#SBATCH --output=output_%x_%j.out
#SBATCH --error=error_%x_%j.err

### Your script for computation ###
module load anaconda

# >>>>> CHANGE THIS: Replace with your conda environment name <<<<<
# Run 'conda info --envs' on the cluster to see available environments
source activate YOUR_ENV_NAME

python sample_perspectives.py
