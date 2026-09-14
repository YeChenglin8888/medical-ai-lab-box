# medical-ai-lab-box

医学人工智能实验箱迁移包。

## 实验箱下载运行

```bash
git clone https://github.com/YeChenglin8888/medical-ai-lab-box.git
cd medical-ai-lab-box
```

实验五推荐使用英文目录：

```bash
cd exp5_xray_pneumonia
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python run_exp5.py --model efficientnet_b0 --epochs 3 --batch-size 4 2>&1 | tee exp5_run.log
```
