#! /bin/bash
PYTHON="$HOME/.pyenv/versions/pcl/bin/python"
# network config
ENCODER="resnet50"
DECODER="attention"
DATASET="raw"
## experimental settings
CLASSIFIER="OR"
INFERENCE="soft"
NUM_CLASSES=80
# dataset
RGB_DIR="/home/shawn/disk/GraduateProject/RAW/"
DEP_DIR="/home/shawn/disk/GraduateProject/RAW/"
TEST_RGB_TXT="../datasets/raw_path/valid_rgb.txt"
TEST_DEP_TXT="../datasets/raw_path/valid_depth.txt"
TEST_RES_DIR="res"
# testing settings
MODE="test"
GPU=True
TEST_USE_FLIP=True
TEST_USE_MS=False
INFERENCE='soft'
# set the output path of checkpoints, training log.
WORKSPACE_DIR="../workspace/"
LOG_DIR="log_${ENCODER}${DECODER}_${DATASET}_${CLASSIFIER}_200108a"
TEST_CHECKPOINT="ResNet_041.pkl"
TEST_RESTORE_FROM="${WORKSPACE_DIR}${LOG_DIR}/${TEST_CHECKPOINT}"
$PYTHON -u depthest_main.py --mode $MODE --encoder $ENCODER --decoder $DECODER --classifier $CLASSIFIER --inference $INFERENCE --classes $NUM_CLASSES \
                            --dataset $DATASET --rgb-dir $RGB_DIR --dep-dir $DEP_DIR --test-rgb $TEST_RGB_TXT --test-dep $TEST_DEP_TXT \
                            --gpu True --use-flip $TEST_USE_FLIP --use-ms $TEST_USE_MS --logdir $LOG_DIR --resdir $TEST_RES_DIR  \
                            --resume $TEST_RESTORE_FROM 