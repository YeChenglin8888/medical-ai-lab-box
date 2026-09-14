# Running The Experiments

## Diabetes Genetic Risk Monitoring

Windows or PC:

```powershell
cd diabetes_genetic_risk_monitoring
python -m pip install -r requirements.txt
python run_diabetes_risk.py
```

Lab box:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate course_dl
cd ~/Desktop/medical-ai-lab-box/diabetes_genetic_risk_monitoring
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python run_diabetes_risk.py 2>&1 | tee run_diabetes_risk.log
```

Outputs are written to:

```text
diabetes_genetic_risk_monitoring/outputs/pc
```

## Chest X-ray Pneumonia Classification

PC with CUDA:

```powershell
cd chest_xray_pneumonia_classification
python -m pip install -r requirements.txt
python run_chest_xray.py --model vit_b_16 --epochs 10 --batch-size 8
```

Lab box CPU:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate course_dl
cd ~/Desktop/medical-ai-lab-box/chest_xray_pneumonia_classification
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python run_chest_xray.py --model efficientnet_b0 --epochs 3 --batch-size 4 2>&1 | tee run_chest_xray.log
```

Outputs are written to:

```text
chest_xray_pneumonia_classification/outputs/pc
```

Saved comparison outputs:

```text
outputs/pc       PC run results
outputs/lab_box  lab box run results
```
