请将胸部X光数据放入本目录下的“教学数据”文件夹，结构如下：

教学数据/
├─ train/
│  ├─ NORMAL/
│  └─ PNEUMONIA/
├─ val/                 可选；没有则程序自动从 train 划分验证集
│  ├─ NORMAL/
│  └─ PNEUMONIA/
└─ test/
   ├─ NORMAL/
   └─ PNEUMONIA/

运行示例：
python "实验五_胸部X光肺炎分类.py" --epochs 5 --batch-size 8

实验箱CPU较慢时可改用：
python "实验五_胸部X光肺炎分类.py" --model efficientnet_b0 --epochs 3 --batch-size 4
