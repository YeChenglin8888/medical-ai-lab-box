# medical-ai-lab-box

Medical AI lab code, datasets, and run outputs for the lab box workflow.

## Repository Layout

```text
diabetes_genetic_risk_monitoring/
  run_diabetes_risk.py
  data/
  outputs/
    pc/
    lab_box/

chest_xray_pneumonia_classification/
  run_chest_xray.py
  data/
  outputs/
    pc/
    lab_box/

docs/
```

## Lab Box Quick Start

```bash
git clone https://github.com/YeChenglin8888/medical-ai-lab-box.git
cd medical-ai-lab-box
```

Diabetes genetic risk monitoring:

```bash
cd diabetes_genetic_risk_monitoring
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python run_diabetes_risk.py 2>&1 | tee run_diabetes_risk.log
```

Chest X-ray pneumonia classification:

```bash
cd ../chest_xray_pneumonia_classification
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python run_chest_xray.py --model efficientnet_b0 --epochs 3 --batch-size 4 2>&1 | tee run_chest_xray.log
```

PC CUDA run:

```powershell
cd chest_xray_pneumonia_classification
python run_chest_xray.py --model vit_b_16 --epochs 10 --batch-size 8
```
