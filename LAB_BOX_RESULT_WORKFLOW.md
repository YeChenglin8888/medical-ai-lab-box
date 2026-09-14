# Lab Box Result Branch Workflow

## Upload Results From The Lab Box

```bash
cd medical-ai-lab-box
git pull origin main
git checkout -b lab-box-results
```

Copy the lab box outputs:

```bash
mkdir -p chest_xray_pneumonia_classification/outputs/lab_box
cp chest_xray_pneumonia_classification/outputs/pc/* chest_xray_pneumonia_classification/outputs/lab_box/

mkdir -p diabetes_genetic_risk_monitoring/outputs/lab_box
cp diabetes_genetic_risk_monitoring/outputs/pc/* diabetes_genetic_risk_monitoring/outputs/lab_box/
```

Commit and push:

```bash
git add .
git commit -m "Add lab box run results"
git push -u origin lab-box-results
```

## Merge On PC

```powershell
cd "C:\Users\YCL\Desktop\医学人工智能\medical-ai-lab-box"
git checkout main
git pull origin main
git fetch origin lab-box-results
git merge origin/lab-box-results
git push origin main
```

When browser login is unavailable on the lab box, copy the result folder back by USB and merge it on PC.
