#!/bin/bash
#SBATCH --partition=UGGPU-TC1
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=360
#SBATCH --job-name=ImageScoring
#SBATCH --output=output_%x_%j.out
#SBATCH --error=error_%x_%j.err

echo "=============================================="
echo "Starting Image Scoring Job"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "=============================================="

module load cuda/12.6

export LD_LIBRARY_PATH=$HOME/.local/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$HOME/.local/lib/python3.12/site-packages/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH

PYTHON_BIN="$HOME/.conda/envs/geocalibenv/bin/python"

echo "Using Python: $PYTHON_BIN"
$PYTHON_BIN --version

echo "CUDA available:"
$PYTHON_BIN -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"

PROJECT_DIR="$HOME/projects/image_scoring"
cd "$PROJECT_DIR" || exit 1

rm -f scoring_checkpoint.json

echo "Running scoring script..."
$PYTHON_BIN score_images.py
EXIT_CODE=$?

echo "=============================================="
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "=============================================="

exit $EXIT_CODE