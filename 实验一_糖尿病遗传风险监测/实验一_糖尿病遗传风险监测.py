from pathlib import Path
import json
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from lightgbm import LGBMClassifier
    from catboost import CatBoostClassifier
except ModuleNotFoundError as exc:
    raise SystemExit(
        "缺少依赖，请先运行: python -m pip install -r requirements.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "数据"
OUT_DIR = BASE_DIR / "运行结果"
RANDOM_STATE = 42
TARGET = "患有糖尿病标识"
ID_COL = "编号"


def read_csv(name):
    path = DATA_DIR / name
    for encoding in ("gbk", "utf-8-sig"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            pass
    return pd.read_csv(path)


def add_features(df):
    out = df.copy()
    for col in ["体重指数", "舒张压", "口服耐糖量测试", "胰岛素释放实验", "肱三头肌皮褶厚度"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["年龄"] = 2026 - pd.to_numeric(out["出生年份"], errors="coerce")
    out["体重指数_异常"] = (out["体重指数"] <= 0).astype(int)
    out["口服耐糖量测试_异常"] = (out["口服耐糖量测试"] < 0).astype(int)
    out["胰岛素释放实验_为0"] = (out["胰岛素释放实验"] == 0).astype(int)
    out["肱三头肌皮褶厚度_为0"] = (out["肱三头肌皮褶厚度"] == 0).astype(int)

    out.loc[out["体重指数"] <= 0, "体重指数"] = np.nan
    out.loc[out["口服耐糖量测试"] < 0, "口服耐糖量测试"] = np.nan
    out.loc[out["胰岛素释放实验"] == 0, "胰岛素释放实验"] = np.nan
    out.loc[out["肱三头肌皮褶厚度"] == 0, "肱三头肌皮褶厚度"] = np.nan
    return out


def write_data_check(train, test):
    rows = []
    for name, df in [("训练集", train), ("测试集", test)]:
        rows.append({"数据集": name, "检查项目": "行列数", "结果": f"{df.shape[0]}行, {df.shape[1]}列"})
        rows.append({"数据集": name, "检查项目": "重复编号", "结果": int(df[ID_COL].duplicated().sum())})
        for col, value in df.isna().sum().items():
            rows.append({"数据集": name, "检查项目": f"{col}缺失值", "结果": int(value)})
    train[TARGET].value_counts().rename_axis("标签").reset_index(name="样本数").to_csv(
        OUT_DIR / "标签分布.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(rows).to_csv(OUT_DIR / "数据检查记录.csv", index=False, encoding="utf-8-sig")


def make_preprocessor():
    numeric_features = [
        "性别",
        "年龄",
        "体重指数",
        "舒张压",
        "口服耐糖量测试",
        "胰岛素释放实验",
        "肱三头肌皮褶厚度",
        "体重指数_异常",
        "口服耐糖量测试_异常",
        "胰岛素释放实验_为0",
        "肱三头肌皮褶厚度_为0",
    ]
    categorical_features = ["糖尿病家族史"]
    return ColumnTransformer(
        [
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_features),
            ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical_features),
        ]
    )


def build_models():
    return {
        "随机森林": RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=300,
            learning_rate=0.03,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            verbosity=-1,
        ),
        "CatBoost": CatBoostClassifier(
            iterations=300,
            learning_rate=0.03,
            depth=6,
            loss_function="Logloss",
            eval_metric="AUC",
            random_seed=RANDOM_STATE,
            verbose=False,
            allow_writing_files=False,
            auto_class_weights="Balanced",
        ),
    }


def metric_row(name, y_true, proba):
    pred = (proba >= 0.5).astype(int)
    fpr, tpr, _ = roc_curve(y_true, proba)
    return {
        "模型": name,
        "Accuracy": round(accuracy_score(y_true, pred), 4),
        "Precision": round(precision_score(y_true, pred, zero_division=0), 4),
        "Recall": round(recall_score(y_true, pred, zero_division=0), 4),
        "F1": round(f1_score(y_true, pred, zero_division=0), 4),
        "AUC": round(auc(fpr, tpr), 4),
    }


def save_plots(y_valid, probas):
    metrics = pd.read_csv(OUT_DIR / "模型评价指标.csv", encoding="utf-8-sig")
    ax = metrics.set_index("模型")[["Accuracy", "Precision", "Recall", "F1", "AUC"]].plot(kind="bar", figsize=(9, 5), ylim=(0, 1))
    ax.set_xlabel("Model")
    ax.set_ylabel("Score")
    ax.set_title("Validation Metrics")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "指标比较图.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 5))
    for name, proba in probas.items():
        fpr, tpr, _ = roc_curve(y_valid, proba)
        plt.plot(fpr, tpr, label=f"{name} AUC={auc(fpr, tpr):.4f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "ROC曲线.png", dpi=180)
    plt.close()

    for name, proba in probas.items():
        cm = confusion_matrix(y_valid, (proba >= 0.5).astype(int))
        ConfusionMatrixDisplay(cm, display_labels=["0", "1"]).plot(cmap="Blues")
        plt.title(name)
        plt.tight_layout()
        plt.savefig(OUT_DIR / f"混淆矩阵_{name}.png", dpi=180)
        plt.close()


def main():
    OUT_DIR.mkdir(exist_ok=True)
    warnings.filterwarnings("ignore", category=UserWarning)

    train_raw = read_csv("比赛训练集.csv")
    test_raw = read_csv("比赛测试集.csv")
    write_data_check(train_raw, test_raw)

    train = add_features(train_raw)
    test = add_features(test_raw)
    y = train[TARGET].astype(int)
    X = train.drop(columns=[TARGET, ID_COL, "出生年份"])
    X_test = test.drop(columns=[ID_COL, "出生年份"])

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    valid_probas = {}
    rows = []
    params = []
    for name, model in build_models().items():
        pipe = Pipeline([("preprocess", make_preprocessor()), ("model", model)])
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_valid)[:, 1]
        valid_probas[name] = proba
        rows.append(metric_row(name, y_valid, proba))
        params.append({"模型": name, "主要参数": json.dumps(model.get_params(), ensure_ascii=False, default=str)})

    valid_probas["软投票融合"] = np.mean(list(valid_probas.values()), axis=0)
    rows.append(metric_row("软投票融合", y_valid, valid_probas["软投票融合"]))
    pd.DataFrame(rows).to_csv(OUT_DIR / "模型评价指标.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(params).to_csv(OUT_DIR / "模型参数记录.csv", index=False, encoding="utf-8-sig")
    save_plots(y_valid, valid_probas)

    test_probas = []
    for name, model in build_models().items():
        pipe = Pipeline([("preprocess", make_preprocessor()), ("model", model)])
        pipe.fit(X, y)
        test_probas.append(pipe.predict_proba(X_test)[:, 1])

    final_proba = np.mean(test_probas, axis=0)
    output = pd.DataFrame(
        {
            ID_COL: test_raw[ID_COL],
            "糖尿病风险概率": np.round(final_proba, 6),
            "类别预测": (final_proba >= 0.5).astype(int),
            "随机森林概率": np.round(test_probas[0], 6),
            "LightGBM概率": np.round(test_probas[1], 6),
            "CatBoost概率": np.round(test_probas[2], 6),
        }
    )
    output.to_csv(OUT_DIR / "测试集预测结果.csv", index=False, encoding="utf-8-sig")

    assert len(output) == len(test_raw)
    assert output[ID_COL].is_unique
    assert output["糖尿病风险概率"].between(0, 1).all()
    assert set(output["类别预测"].unique()) <= {0, 1}
    print("实验一完成，结果已保存到:", OUT_DIR)


if __name__ == "__main__":
    main()
