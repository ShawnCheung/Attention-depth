##+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
## Created by: chenyuru
## This source code is licensed under the MIT-style license
##+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import os
import sys
#sys.path.append(os.path.dirname(__file__))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from collections import OrderedDict
try:
    from .sadecoder import SADecoder
except:
    from sadecoder import SADecoder

def continuous2discrete(depth, d_min, d_max, n_c):
    mask = ~((depth > d_min) * (depth < d_max))
    depth = torch.round(torch.log(depth / d_min) / np.log(d_max / d_min) * (n_c - 1))
    depth[mask] = 0
    return depth

def discrete2continuous(depth, d_min, d_max, n_c):
    depth = torch.exp(depth / (n_c - 1) * np.log(d_max / d_min) + np.log(d_min))
    return depth

class BaseClassificationModel_(nn.Module):
    def __init__(self, min_depth, max_depth, num_classes, 
                 classifierType, inferenceType, decoderType):
        super().__init__()
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.num_classes = num_classes
        self.classifierType = classifierType
        self.inferenceType = inferenceType
        self.decoderType = decoderType

    def decode_ord(self, y):
        batch_size, prob, height, width = y.shape
        y = torch.reshape(y, (batch_size, prob//2, 2, height, width))
        denominator = torch.sum(torch.exp(y), 2)
        pred_score = torch.div(torch.exp(y[:, :, 1, :, :]), denominator)
        return pred_score

    def hard_cross_entropy(self, pred_score, d_min, d_max, n_c):
        pred_label = torch.argmax(pred_score, 1, keepdim=True).float()
        pred_depth = discrete2continuous(pred_label, d_min, d_max, n_c)
        return pred_depth

    def soft_cross_entropy(self, pred_score, d_min, d_max, n_c):
        pred_prob = F.softmax(pred_score, dim=1).permute((0, 2, 3, 1))
        weight = torch.arange(n_c).float().cuda()
        weight = weight * np.log(d_max / d_min) / (n_c - 1) + np.log(d_min)
        weight = weight.unsqueeze(-1)
        output = torch.exp(torch.matmul(pred_prob, weight))
        output = output.permute((0, 3, 1, 2))
        return output

    def hard_ordinal_regression(self, pred_prob, d_min, d_max, n_c):
        mask = (pred_prob > 0.5).float()
        pred_label = torch.sum(mask, 1, keepdim=True)
        #pred_label = torch.round(torch.sum(pred_prob, 1, keepdim=True))
        pred_depth = (discrete2continuous(pred_label, d_min, d_max, n_c) +
                      discrete2continuous(pred_label + 1, d_min, d_max, n_c)) / 2
        return pred_depth

    def soft_ordinal_regression(self, pred_prob, d_min, d_max, n_c):
        pred_prob_sum = torch.sum(pred_prob, 1, keepdim=True)
        Intergral = torch.floor(pred_prob_sum)
        Fraction = pred_prob_sum - Intergral
        depth_low = (discrete2continuous(Intergral, d_min, d_max, n_c) +
                     discrete2continuous(Intergral + 1, d_min, d_max, n_c)) / 2
        depth_high = (discrete2continuous(Intergral + 1, d_min, d_max, n_c) +
                      discrete2continuous(Intergral + 2, d_min, d_max, n_c)) / 2
        pred_depth = depth_low * (1 - Fraction) + depth_high * Fraction
        return pred_depth

    def inference(self, y):
        if isinstance(y, list):
            y = y[-1]
        if isinstance(y, dict):
            y = y['y']
        # mode
        # OR = Ordinal Regression
        # CE = Cross Entropy
        if self.classifierType == 'OR':
            if self.inferenceType == 'soft':
                inferenceFunc = self.soft_ordinal_regression
            else:    # hard OR
                inferenceFunc = self.hard_ordinal_regression
        else:  # 'CE'
            if self.inferenceType == 'soft': # soft CE
                inferenceFunc = self.soft_cross_entropy
            else:     # hard CE
                inferenceFunc = self.hard_cross_entropy
        pred_depth = inferenceFunc(y, self.min_depth, self.max_depth, self.num_classes)
        return pred_depth

    def forward():
        raise NotImplementedError

    
def make_decoder(height, width, command='attention'):
    #command = eval(command)
    if command == 'attention':
        dec = SADecoder(height=height, width=width)
    else:
        raise RuntimeError('decoder not found. The decoder must be attention.')
    return dec

def make_classifier(classifierType='OR', num_classes=80, use_inter=False, channel1=1024, channel2=2048):
    classes = 2 * num_classes if classifierType == 'OR' else num_classes
    interout = None
    if use_inter:
        interout = nn.Sequential(OrderedDict([
            ('dropout1', nn.Dropout2d(0.2, inplace=True)),
            ('conv1',    nn.Conv2d(channel1, channel1//2, kernel_size=3, stride=1, padding=1)),
            ('relu',     nn.ReLU(inplace=True)),
            ('dropout2', nn.Dropout2d(0.2, inplace=False)),
            ('upsample', nn.Upsample(scale_factor=8, mode='bilinear', align_corners=True))]))
    classifier = nn.Sequential(OrderedDict([
        ('conv',     nn.Conv2d(channel2, classes, kernel_size=1, stride=1, padding=0)),
        ('upsample', nn.Upsample(scale_factor=8, mode='bilinear', align_corners=True))]))
    return [interout, classifier]

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, dilation=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, dilation=dilation,
                               padding=dilation, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

class ResNet(BaseClassificationModel_):
    def __init__(self, min_depth, max_depth, num_classes,
                 classifierType, inferenceType, decoderType,
                 height, width,
                 alpha=0, beta=0,
                 layers=[3, 4, 6, 3], 
                 block=Bottleneck):
        # Note: classifierType: CE=Cross Entropy, OR=Ordinal Regression
        super(ResNet, self).__init__(min_depth, max_depth, num_classes, 
                                     classifierType, inferenceType, decoderType)
        self.inplanes = 64
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7,stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu1 = nn.ReLU(True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=1, dilation=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=1, dilation=4)

        self.alpha = alpha
        self.beta = beta
        self.decoder = make_decoder(height, width, decoderType)
        self.use_inter = self.alpha != 0.0
        self.interout, self.classifier = make_classifier(classifierType, num_classes, self.use_inter, channel1=1024, channel2=2048)
        self.parameter_initialization()

    def parameter_initialization(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight.data, nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias.data, 0)
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1, dilation=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )
        layers = []
        layers.append(block(self.inplanes, planes, stride=stride,
                            dilation=dilation, downsample=downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes,
                                stride=1, dilation=dilation))
        return nn.Sequential(*layers)

    def forward(self, x):
        temp = x
        x = self.relu1(self.bn1(self.conv1(x))) #[1, 64, 200, 320]
        if torch.isnan(x).sum()!=0:
            import pdb;pdb.set_trace()
        x = self.maxpool(x)  #[1, 64, 100, 160]
        x = self.layer1(x) #[1, 256, 100, 160]
        x = self.layer2(x) #[1, 512, 50, 80]
        x = self.layer3(x) #[1, 1024, 50, 80]
        
        inter_y = None
        if self.use_inter:
            inter_y = self.interout(x)
        x = self.layer4(x)  #[1, 2048, 50, 80]
        if self.decoderType == 'attention':
            x, sim_map = self.decoder(x) #[1, 2048, 50, 80], [1, 4000, 4000]
        y = self.classifier(x) #[1, 160, 400, 640]

        if self.classifierType == 'OR':
            y = self.decode_ord(y)
            if self.use_inter:
                inter_y = self.decode_ord(inter_y)
        
        return {'inter_y': inter_y, 'sim_map': sim_map, 'y': y}

    class LossFunc(nn.Module):
        def __init__(self, min_depth, max_depth, num_classes, 
                     AppearanceLoss=None, AuxiliaryLoss=None, AttentionLoss=None,
                     alpha=0., beta=0.):
            super(ResNet.LossFunc, self).__init__()
            self.min_depth = min_depth
            self.max_depth = max_depth
            self.num_classes = num_classes
            self.alpha = alpha
            self.beta = beta
            self.AppearanceLoss = AppearanceLoss
            self.AuxiliaryLoss = AuxiliaryLoss
            self.AttentionLoss = AttentionLoss

        def forward(self, preds, label, epoch):
            """
            Parameter
            ---------
            preds: [batch_size, c, h, w] * 2 + sim_map
            label: [batch_size, 1, h, w]
            sim_map 
            """
            inter_y = preds['inter_y']
            sim_map = preds['sim_map']
            y = preds['y']
            dis_label = continuous2discrete(label, self.min_depth, self.max_depth, self.num_classes)
            # image loss
            
            loss1 = self.AppearanceLoss(y, dis_label.squeeze(1).long())
            # intermediate supervision loss
            loss2 = 0
            if self.alpha != 0.:
                loss2 = self.AuxiliaryLoss(inter_y, dis_label.squeeze(1).long())
            # attention loss
            loss3 = 0
            if self.beta != 0.:
                loss3 = self.AttentionLoss(sim_map, dis_label)
            total_loss = loss1 + self.alpha * loss2 + self.beta * loss3
            return loss1, loss2, loss3, total_loss
    
if __name__ == '__main__':
    net_kwargs = {'min_depth': 0, 'max_depth': 10, 'num_classes': 80,
                  'classifierType': 'OR', 'inferenceType': 'soft', 'decoderType': 'attention',
                  'height': 160, 'width': 640,
                  'alpha': 0, 'beta': 0, 'layers': [3, 4, 6, 3]}

    net = ResNet(**net_kwargs)

    image = torch.rand(1, 3, 224, 304)
    output = net(image)
    print(output['sim_map'].shape)
    print(output['y'].shape)