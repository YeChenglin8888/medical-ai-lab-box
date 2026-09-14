# Results Summary

## Diabetes Genetic Risk Monitoring

| Environment | Model | Accuracy | Precision | Recall | F1 | AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PC | Random Forest | 0.9586 | 0.9412 | 0.9509 | 0.9460 | 0.9905 |
| PC | LightGBM | 0.9576 | 0.9365 | 0.9535 | 0.9449 | 0.9932 |
| PC | CatBoost | 0.9596 | 0.9391 | 0.9561 | 0.9475 | 0.9917 |
| PC | Soft Voting | 0.9596 | 0.9369 | 0.9587 | 0.9476 | 0.9921 |
| Lab Box | Random Forest | 0.9586 | 0.9412 | 0.9509 | 0.9460 | 0.9896 |
| Lab Box | LightGBM | 0.9576 | 0.9365 | 0.9535 | 0.9449 | 0.9932 |
| Lab Box | CatBoost | 0.9596 | 0.9391 | 0.9561 | 0.9475 | 0.9917 |
| Lab Box | Soft Voting | 0.9606 | 0.9370 | 0.9612 | 0.9490 | 0.9920 |

## Chest X-ray Pneumonia Classification

| Environment | Model | Epochs | Batch Size | Device | Runtime Seconds | Accuracy | Precision | Recall | F1 |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| PC | ViT-B/16 | 10 | 8 | CUDA | 33.60 | 0.9099 | 0.9388 | 0.8679 | 0.9020 |
| Lab Box | ConvNeXt Tiny | 5 | 8 | CPU | 397.65 | 0.8649 | 0.8958 | 0.8113 | 0.8515 |

## Report Notes

The PC run used a CUDA-capable GPU and a Vision Transformer model, while the lab box run used CPU execution. The chest X-ray comparison should therefore be discussed as both a model comparison and a hardware/runtime comparison.
