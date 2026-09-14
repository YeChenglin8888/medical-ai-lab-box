from pathlib import Path
import csv

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ASSETS = REPORTS / "_assets"
MODEL_EN = {"随机森林": "Random Forest", "软投票融合": "Soft Voting"}


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def count_files(path):
    return sum(1 for p in path.iterdir() if p.is_file())


def fmt(value):
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)


def set_cell(cell, text, bold=False, center=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(str(text))
    run.bold = bold
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(9)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def borders(table):
    tbl_pr = table._tbl.tblPr
    tbl_borders = tbl_pr.first_child_found_in("w:tblBorders")
    if tbl_borders is None:
        tbl_borders = OxmlElement("w:tblBorders")
        tbl_pr.append(tbl_borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        el = tbl_borders.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            tbl_borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "D9D9D9")


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = True
    for i, h in enumerate(headers):
        set_cell(table.rows[0].cells[i], h, bold=True, center=True)
        shade(table.rows[0].cells[i], "D9EAF7")
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], value, center=i != 0)
    borders(table)
    doc.add_paragraph()
    return table


def set_styles(doc):
    sec = doc.sections[0]
    sec.top_margin = Inches(0.75)
    sec.bottom_margin = Inches(0.75)
    sec.left_margin = Inches(0.82)
    sec.right_margin = Inches(0.82)
    for name, size in [("Normal", 10.5), ("Title", 18), ("Heading 1", 14), ("Heading 2", 12)]:
        style = doc.styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.color.rgb = None
        p_pr = style._element.get_or_add_pPr()
        p_bdr = p_pr.find(qn("w:pBdr"))
        if p_bdr is not None:
            p_pr.remove(p_bdr)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.15
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)


def h(doc, text, level=1):
    doc.add_heading(text, level=level)


def p(doc, text):
    doc.add_paragraph(text)


def pic(doc, path, caption, width=5.7):
    if path.exists():
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.add_run().add_picture(str(path), width=Inches(width))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in cap.runs:
            r.font.size = Pt(9)


def make_diabetes_figures(metrics):
    ASSETS.mkdir(exist_ok=True)
    labels = [MODEL_EN.get(r["模型"], r["模型"]) for r in metrics]
    colors = {"Accuracy": "#1f77b4", "Precision": "#ff7f0e", "Recall": "#2ca02c", "F1": "#d62728", "AUC": "#9467bd"}
    img = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 26)
    small = ImageFont.truetype("arial.ttf", 22)
    left, top, right, bottom = 100, 90, 1080, 560
    draw.text((left, 25), "PC Validation Metrics", fill="black", font=font)
    draw.line([(left, top), (left, bottom), (right, bottom)], fill="black", width=3)
    for yv in [0.90, 0.925, 0.95, 0.975, 1.00]:
        y = bottom - int((yv - 0.90) / 0.10 * (bottom - top))
        draw.line([(left, y), (right, y)], fill="#dddddd", width=1)
        draw.text((25, y - 12), f"{yv:.3f}", fill="black", font=small)
    xs = [left + int((right - left) * i / (len(labels) - 1)) for i in range(len(labels))]
    for i, label in enumerate(labels):
        draw.text((xs[i] - 55, bottom + 20), label, fill="black", font=small)
    for key, color in colors.items():
        pts = []
        for x, r in zip(xs, metrics):
            y = bottom - int((float(r[key]) - 0.90) / 0.10 * (bottom - top))
            pts.append((x, y))
        draw.line(pts, fill=color, width=4)
        for pt in pts:
            draw.ellipse((pt[0] - 6, pt[1] - 6, pt[0] + 6, pt[1] + 6), fill=color)
    for i, (key, color) in enumerate(colors.items()):
        x = left + i * 185
        draw.rectangle((x, 620, x + 25, 645), fill=color)
        draw.text((x + 35, 617), key, fill="black", font=small)
    metrics_path = ASSETS / "diabetes_pc_metrics.png"
    img.save(metrics_path)

    matrix = [[602, 25], [15, 372]]
    img = Image.new("RGB", (900, 760), "white")
    draw = ImageDraw.Draw(img)
    draw.text((120, 35), "Lab Box Soft Voting Confusion Matrix", fill="black", font=font)
    x0, y0, size = 220, 150, 230
    max_v = max(max(row) for row in matrix)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            shade_v = 245 - int(value / max_v * 165)
            fill = (shade_v, shade_v + 5, 255)
            x, y = x0 + j * size, y0 + i * size
            draw.rectangle((x, y, x + size, y + size), fill=fill, outline="black", width=3)
            draw.text((x + 95, y + 95), str(value), fill="black", font=font)
    draw.text((x0 + 65, y0 - 45), "Pred 0", fill="black", font=small)
    draw.text((x0 + size + 65, y0 - 45), "Pred 1", fill="black", font=small)
    draw.text((x0 - 100, y0 + 100), "True 0", fill="black", font=small)
    draw.text((x0 - 100, y0 + size + 100), "True 1", fill="black", font=small)
    cm_path = ASSETS / "diabetes_lab_soft_voting_confusion.png"
    img.save(cm_path)
    return metrics_path, cm_path


def make_diabetes():
    base = ROOT / "diabetes_genetic_risk_monitoring"
    pc = base / "outputs" / "pc"
    lab = base / "outputs" / "lab_box"
    pc_metrics = read_csv(pc / "metrics.csv")
    lab_metrics = read_csv(lab / "metrics.csv")
    metric_fig, cm_fig = make_diabetes_figures(pc_metrics)
    dist = read_csv(pc / "label_distribution.csv")
    data_check = read_csv(pc / "data_check.csv")

    doc = Document()
    set_styles(doc)
    doc.add_paragraph("实验一报告", style="Title")
    p(doc, "本实验围绕糖尿病遗传风险监测任务，完成数据检查、缺失值处理、模型训练、模型融合与结果对比。结果显示，树模型在结构化医学特征上表现稳定，软投票融合模型在实验箱端取得最高 F1 值 0.9490。")

    h(doc, "一 实验目的")
    p(doc, "读取训练集和测试集，检查编号重复、字段缺失和标签分布；在避免数据泄漏的前提下完成预处理，并比较随机森林、LightGBM、CatBoost 与软投票融合模型在糖尿病风险分类任务中的效果。")

    h(doc, "二 数据与预处理")
    train_n = sum(int(r["样本数"]) for r in dist)
    rows = [["训练集", f"{train_n} 条", "含糖尿病标签"], ["测试集", "1000 条", "无标签，用于生成预测结果"]]
    add_table(doc, ["数据集", "规模", "说明"], rows)
    add_table(doc, ["标签", "样本数"], [[r["标签"], r["样本数"]] for r in dist])
    miss = [r for r in data_check if "缺失值" in r["检查项目"] and r["结果"] != "0"]
    add_table(doc, ["检查项", "结果"], [[r["数据集"] + " " + r["检查项目"], r["结果"]] for r in miss])
    p(doc, "舒张压存在少量缺失值，实验中使用训练集拟合的预处理流程完成填补与编码，并将同一流程应用到验证集和测试集，避免把验证或测试信息提前泄漏到训练过程。")
    doc.add_page_break()

    h(doc, "三 模型方法")
    p(doc, "随机森林用于提供稳健的树集成基线；LightGBM 和 CatBoost 用于处理非线性特征组合与类别特征；软投票融合对三个模型输出概率求平均，得到最终风险概率和二分类结果。评价指标采用 Accuracy、Precision、Recall、F1 和 AUC。")
    add_table(doc, ["模型", "主要作用"], [["随机森林", "树集成基线，抗过拟合能力较好"], ["LightGBM", "梯度提升模型，训练速度快"], ["CatBoost", "梯度提升模型，对类别特征处理友好"], ["软投票融合", "融合三类模型概率，提升稳定性"]])

    h(doc, "四 实验结果")
    headers = ["环境", "模型", "Accuracy", "Precision", "Recall", "F1", "AUC"]
    rows = []
    for env, metrics in [("PC", pc_metrics), ("实验箱", lab_metrics)]:
        for r in metrics:
            rows.append([env, r["模型"], fmt(r["Accuracy"]), fmt(r["Precision"]), fmt(r["Recall"]), fmt(r["F1"]), fmt(r["AUC"])])
    add_table(doc, headers, rows)
    pic(doc, metric_fig, "图 1 PC 端不同模型指标对比")
    pic(doc, cm_fig, "图 2 实验箱端软投票融合混淆矩阵", width=4.8)

    h(doc, "五 结果分析")
    p(doc, "PC 端与实验箱端的结果整体一致，说明迁移后的代码、数据划分和依赖环境能够复现实验。实验箱端软投票融合模型 Accuracy 为 0.9606、Recall 为 0.9612、F1 为 0.9490，略高于单模型，说明融合模型能够减少单一模型波动。AUC 最高的是 LightGBM，为 0.9932，说明该模型的概率排序能力最强；最终预测采用软投票更重视综合稳定性。")

    h(doc, "六 结论")
    p(doc, "本实验完成了糖尿病遗传风险监测的完整机器学习流程。树模型对该结构化数据任务适配良好，软投票融合在实验箱端取得最优综合表现，可作为最终测试集预测方案。")

    out = REPORTS / "diabetes_genetic_risk_monitoring_report.docx"
    doc.save(out)
    return out


def make_chest():
    base = ROOT / "chest_xray_pneumonia_classification"
    pc = base / "outputs" / "pc"
    lab = base / "outputs" / "lab_box"
    pc_metrics = read_csv(pc / "metrics.csv")[0]
    lab_metrics = read_csv(lab / "metrics.csv")[0]
    pc_last = read_csv(pc / "training_history.csv")[-1]
    lab_last = read_csv(lab / "training_history.csv")[-1]

    doc = Document()
    set_styles(doc)
    doc.add_paragraph("实验五报告", style="Title")
    p(doc, "本实验完成胸部 X 光片肺炎二分类任务。PC 端使用 CUDA 环境训练 Vision Transformer，实验箱端使用 CPU 训练 ConvNeXt Tiny。PC 端 ViT 在测试集上取得 Accuracy 0.9099、F1 0.9020，整体优于实验箱端 ConvNeXt Tiny。")

    h(doc, "一 实验目的")
    p(doc, "基于胸部 X 光图像训练深度学习分类模型，判断样本属于 NORMAL 或 PNEUMONIA。实验重点包括数据读取、图像预处理、迁移学习训练、验证集监控、测试集评估以及 PC 与实验箱运行结果对比。")

    h(doc, "二 数据集")
    rows = []
    for split in ["train", "val", "test"]:
        for label in ["NORMAL", "PNEUMONIA"]:
            rows.append([split, label, str(count_files(base / "data" / split / label))])
    add_table(doc, ["划分", "类别", "图像数"], rows)
    p(doc, "训练集样本较少，验证集也只有 16 张图像，因此单轮验证 F1 波动较大。报告中的主要结论以测试集指标为准。")

    h(doc, "三 模型方法")
    p(doc, "PC 端选择 vit_b_16，利用 CUDA 和预训练权重进行迁移学习。ViT 将图像切分为 patch 后通过 Transformer 自注意力建模全局关系，适合在 GPU 上进行较快实验。实验箱端受 CPU 性能限制，使用 convnext_tiny 完成可复现实验。损失函数为交叉熵，学习率为 0.0001，批量大小为 8。")
    add_table(doc, ["环境", "模型", "轮数", "设备", "运行时间秒"], [["PC", pc_metrics["模型"], pc_metrics["训练轮数"], pc_metrics["设备"], pc_metrics["运行秒数"]], ["实验箱", lab_metrics["模型"], lab_metrics["训练轮数"], lab_metrics["设备"], lab_metrics["运行秒数"]]])

    h(doc, "四 实验结果")
    add_table(doc, ["环境", "模型", "Accuracy", "Precision", "Recall", "F1"], [["PC", pc_metrics["模型"], fmt(pc_metrics["Accuracy"]), fmt(pc_metrics["Precision"]), fmt(pc_metrics["Recall"]), fmt(pc_metrics["F1"])], ["实验箱", lab_metrics["模型"], fmt(lab_metrics["Accuracy"]), fmt(lab_metrics["Precision"]), fmt(lab_metrics["Recall"]), fmt(lab_metrics["F1"])]])
    add_table(doc, ["环境", "最终训练损失", "最终验证损失", "最终验证 F1"], [["PC", fmt(pc_last["train_loss"]), fmt(pc_last["val_loss"]), fmt(pc_last["val_f1"])], ["实验箱", fmt(lab_last["train_loss"]), fmt(lab_last["val_loss"]), fmt(lab_last["val_f1"])]])
    pic(doc, pc / "loss_curve.png", "图 1 PC 端 ViT 训练损失曲线")
    pic(doc, pc / "confusion_matrix.png", "图 2 PC 端 ViT 测试集混淆矩阵")
    pic(doc, lab / "loss_curve.png", "图 3 实验箱端 ConvNeXt Tiny 训练损失曲线")
    pic(doc, lab / "confusion_matrix.png", "图 4 实验箱端 ConvNeXt Tiny 测试集混淆矩阵")

    h(doc, "五 结果分析")
    p(doc, "PC 端 ViT 的 Accuracy 为 0.9099，F1 为 0.9020；实验箱端 ConvNeXt Tiny 的 Accuracy 为 0.8649，F1 为 0.8515。PC 端结果更好，主要原因是模型结构更偏向全局图像关系建模，同时 CUDA 使 10 轮训练只耗时 33.6 秒，能够进行更充分的训练。实验箱端 CPU 运行 5 轮耗时 397.65 秒，训练轮数和模型选择都更保守。")
    p(doc, "从医学筛查角度看，Recall 代表肺炎样本被检出的比例。PC 端 Recall 为 0.8679，高于实验箱端 0.8113，漏检风险更低；但本实验数据规模有限，模型输出不能替代临床诊断，只能作为课程实验中的图像分类验证。")

    h(doc, "六 结论")
    p(doc, "本实验完成胸片肺炎分类的迁移学习流程。PC 端使用 Vision Transformer 能充分利用 GPU，并取得更好的测试集表现；实验箱端结果则验证了项目在低算力环境中的可迁移性。后续报告撰写和答辩可将两端结果作为模型选择与硬件差异分析依据。")

    out = REPORTS / "chest_xray_pneumonia_classification_report.docx"
    doc.save(out)
    return out


def main():
    REPORTS.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    for path in [make_diabetes(), make_chest()]:
        print(path)


if __name__ == "__main__":
    main()
