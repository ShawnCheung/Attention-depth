#! /bin/bash
# check gpu info
nvidia-smi
# pytorch 04
PYTHON="$HOME/.pyenv/versions/pcl/bin/python"
##### experimental settings
# network config
ENCODER="resnet50"
DECODER="attention"
DATASET="raw"
NUM_CLASSES=80
# datasets
# replace the DATA_DIR with your folder path to the dataset.
RGB_DIR="/home/shawn/disk/GraduateProject/RAW/"
DEP_DIR="/home/shawn/disk/GraduateProject/RAW/"
TRAIN_RGB_TXT="../datasets/raw_path/train_rgb.txt"
TRAIN_DEP_TXT="../datasets/raw_path/train_depth.txt" 
VAL_RGB_TXT="../datasets/raw_path/valid_rgb.txt"
VAL_DEP_TXT="../datasets/raw_path/valid_depth.txt"
# training settings
MODE="train"
GPU=True
EPOCHES=50
LR=2e-5
FINAL_LR=2e-3
WEIGHT_DECAY=5e-4
BATCHSIZE=3
BATCHSIZEVAL=5
EVAL_FREQ=1
THREADS=4
OPTIMIZER="sgd"
SCHEDULER="poly"
POWER=0.9
FLIP=False
JITTER=True
CROP=False
ROTATE=False
SCALE=False
USE_WEIGHTS=False
CLASSIFIER="OR"
INFERENCE="soft"
EPS=0.0
PRIOR="gaussian"
OHEMTHRES=0.7
OHEMKEEP=100000
ALPHA=0
BETA=0
# set the output path of checkpoints, training log.
WORKSPACE_DIR="../workspace/"
LOG_DIR="log_${ENCODER}${DECODER}_${DATASET}_${CLASSIFIER}_200108a"
PRETRAIN=True
#RESUME="${WORKSPACE_DIR}log_${ENCODER}${DECODER}_${DATASET}_${CLASSIFIER}_200106a/best.pkl"
########################################################################################################################
#  Training
########################################################################################################################
$PYTHON -u depthest_main.py --mode $MODE --encoder $ENCODER --decoder $DECODER --classifier $CLASSIFIER --inference $INFERENCE \
                            --classes $NUM_CLASSES --epochs $EPOCHES --eval-freq $EVAL_FREQ --threads $THREADS \
                            --dataset $DATASET --rgb-dir $RGB_DIR --dep-dir $DEP_DIR --train-rgb $TRAIN_RGB_TXT --train-dep $TRAIN_DEP_TXT \
                            --val-rgb $VAL_RGB_TXT --val-dep $VAL_DEP_TXT --batch  $BATCHSIZE --batch-val $BATCHSIZEVAL \
                            --optimizer $OPTIMIZER --weight-decay $WEIGHT_DECAY --lr $LR --final-lr $FINAL_LR --gpu $GPU \
                            --scheduler $SCHEDULER --power $POWER \
                            --random-flip $FLIP --random-jitter $JITTER --random-crop $CROP --random-scale $SCALE --random-rotate $ROTATE \
                            --workdir $WORKSPACE_DIR --logdir $LOG_DIR --pretrain $PRETRAIN --eps $EPS --prior $PRIOR --use-weights $USE_WEIGHTS \
                            --ohem-thres $OHEMTHRES --ohem-keep $OHEMKEEP --alpha $ALPHA --beta $BETA 

########################################################################################################################
#  Testing
########################################################################################################################
# dataset
# TEST_RGB_TXT="../datasets/nyu_path/valid_rgb.txt"
# TEST_DEP_TXT="../datasets/nyu_path/valid_depth.txt"
# TEST_RES_DIR="res"
# # testing settings
# MODE="test"
# GPU=True
# TEST_USE_FLIP=True
# TEST_USE_MS=False
# INFERENCE='soft'
# TEST_CHECKPOINT="best.pkl"
# TEST_RESTORE_FROM="${WORKSPACE_DIR}${LOG_DIR}/${TEST_CHECKPOINT}"
# $PYTHON -u depthest_main.py --mode $MODE --encoder $ENCODER --decoder $DECODER --classifier $CLASSIFIER --inference $INFERENCE --classes $NUM_CLASSES \
#                             --dataset $DATASET --rgb-dir $RGB_DIR --dep-dir $DEP_DIR --test-rgb $TEST_RGB_TXT --test-dep $TEST_DEP_TXT \
#                             --gpu $GPU --use-flip $TEST_USE_FLIP --use-ms $TEST_USE_MS --logdir $LOG_DIR --resdir $TEST_RES_DIR  \
#                             --resume $TEST_RESTORE_FROM 


