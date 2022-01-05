import os

rgb_valid = open("./valid_rgb.txt", 'w')
depth_valid = open("./valid_depth.txt", 'w')

rgb_train = open("./train_rgb.txt", 'w')
depth_train = open("./train_depth.txt", 'w')

with open("/home/shawn/disk/GraduateProject/RAW/test.txt", 'r') as f:
    lines = f.readlines()
    for line in lines:
        rgb = "imgs/"+line[0:6]+".jpg"+line[6]
        depth = "depths/dense/npy/"+line[0:6]+".npy"+line[6]

        rgb_valid.writelines(rgb)
        depth_valid.writelines(depth)

with open("/home/shawn/disk/GraduateProject/RAW/train.txt", 'r') as f:
    lines = f.readlines()
    for line in lines:
        rgb = "imgs/"+line[0:6]+".jpg"+line[6]
        depth = "depths/dense/npy/"+line[0:6]+".npy"+line[6]

        rgb_train.writelines(rgb)
        depth_train.writelines(depth)

    