from __future__ import annotations
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parent
source = ROOT / "data" / "archive-results.json"
out = ROOT / "output" / "pdf" / "archive-analysis-report.pdf"
data = json.loads(source.read_text(encoding="utf-8"))
pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CNTitle", parent=styles["Title"], fontName="SimHei", fontSize=20, leading=26, alignment=TA_CENTER, textColor=colors.HexColor("#183B56"), spaceAfter=10))
styles.add(ParagraphStyle(name="CNH1", parent=styles["Heading1"], fontName="SimHei", fontSize=14, leading=20, textColor=colors.HexColor("#183B56"), spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name="CNH2", parent=styles["Heading2"], fontName="SimHei", fontSize=11, leading=16, textColor=colors.HexColor("#2F6690"), spaceBefore=7, spaceAfter=4))
styles.add(ParagraphStyle(name="CNBody", parent=styles["BodyText"], fontName="SimHei", fontSize=9.2, leading=14, spaceAfter=5))
styles.add(ParagraphStyle(name="CNSmall", parent=styles["BodyText"], fontName="SimHei", fontSize=7.6, leading=11, textColor=colors.HexColor("#44546A")))
styles.add(ParagraphStyle(name="CNMono", parent=styles["Code"], fontName="SimHei", fontSize=7.5, leading=10, backColor=colors.HexColor("#F4F7FA"), borderPadding=4))

def P(text, style="CNBody"):
    return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"), styles[style])

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("SimHei", 7); canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(18*mm, 10*mm, "Lacan-Agent · Archive Analysis Record · Mock workflow")
    canvas.drawRightString(192*mm, 10*mm, f"第 {doc.page} 页")
    canvas.restoreState()

def status_label(s):
    return {"NEEDS_HUMAN_REVIEW":"等待人工审核", "INGESTED":"已导入，尚未完成分析"}.get(s, s)

completed = [x for x in data if x["state"] == "NEEDS_HUMAN_REVIEW"]
pending = [x for x in data if x["state"] != "NEEDS_HUMAN_REVIEW"]

doc = SimpleDocTemplate(str(out), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm, title="Archive Analysis Record", author="Lacan-Agent")
story=[]
story += [P("聊天文本分析记录", "CNTitle"), P("Lacan-Agent P0 本地 Mock 工作流导出", "CNH2"), Spacer(1, 3*mm)]
story += [P("生成日期：2026-10-09"), P("数据范围：用户提供的六份聊天文本；本报告只导出当前数据库中已经生成的分析记录。", "CNBody")]
summary = [[P("指标", "CNSmall"), P("数量", "CNSmall"), P("说明", "CNSmall")], [P("已完成分析", "CNSmall"), P(str(len(completed)), "CNSmall"), P("运行到 NEEDS_HUMAN_REVIEW，尚未人工批准", "CNSmall")], [P("部分完成", "CNSmall"), P(str(len(pending)), "CNSmall"), P("已导入但未形成完整 Analysis Packet", "CNSmall")], [P("已批准导出", "CNSmall"), P("0", "CNSmall"), P("当前没有生成可执行叙事算子", "CNSmall")]]
t=Table(summary, colWidths=[35*mm, 18*mm, 112*mm]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DCEAF4")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B8C7D9")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5)])); story += [t]
story += [Spacer(1,4*mm), P("重要限制", "CNH1"), P("本批记录使用内置 FakeProvider。观察、假说和反例是流程验证用的结构化模板，不应被解释为对真实人物的临床判断或充分的文本阐释。原始文本中的任何指令性句子均按不可信原文处理。", "CNBody")]

story += [P("运行总览", "CNH1")]
rows=[[P("来源文件", "CNSmall"),P("运行 ID", "CNSmall"),P("参与者", "CNSmall"),P("状态", "CNSmall")]]
for x in data: rows.append([P(x.get("source",""),"CNSmall"),P(x["run_id"],"CNSmall"),P(x["participant_id"],"CNSmall"),P(status_label(x["state"]),"CNSmall")])
t=Table(rows,colWidths=[74*mm,40*mm,27*mm,33*mm],repeatRows=1); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DCEAF4")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B8C7D9")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)])); story += [t, PageBreak()]

for idx,x in enumerate(data,1):
    story += [P(f"记录 {idx}：{x.get('source','未知来源')}", "CNH1"), P(f"运行 ID：{x['run_id']}　参与者隔离 ID：{x['participant_id']}　状态：{status_label(x['state'])}", "CNSmall")]
    if not x.get("observations"):
        story += [P("当前记录只完成了文档导入和初始审计，尚无观察、假说或反例可导出。", "CNBody")]
    else:
        story += [P("观察（Observation）", "CNH2")]
        for o in x["observations"]:
            story += [P(f"{o['id']}：{o['label']}", "CNBody")]
            for ev in o.get("evidence",[]):
                story += [P(f"证据跨度 {ev['span_id']}：{ev['excerpt']}", "CNMono")]
        story += [P("理论假说（Hypothesis）", "CNH2")]
        for h in x["hypotheses"]:
            story += [P(f"{h['id']} · 概念：{', '.join(h.get('concept_ids',[]))} · 状态：{h.get('status','')}", "CNBody"), P(f"替代解释：{'；'.join(h.get('alternatives',[]))}", "CNBody"), P(f"反例/缺口：{'；'.join(h.get('counterexamples',[]))}", "CNBody"), P(f"理论引用跨度：{', '.join(h.get('theory_reference_ids',[]))}", "CNSmall")]
    story += [P("审计轨迹", "CNH2")]
    audit_rows=[[P("阶段", "CNSmall"),P("操作者", "CNSmall"),P("原因", "CNSmall")]]
    for a in x.get("audit",[]): audit_rows.append([P(status_label(a.get("state","")),"CNSmall"),P(a.get("actor",""),"CNSmall"),P(a.get("reason",""),"CNSmall")])
    t=Table(audit_rows,colWidths=[48*mm,32*mm,94*mm],repeatRows=1); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EEF4F8")),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#C9D5E1")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)])); story += [t]
    if idx < len(data): story += [PageBreak()]

story += [PageBreak(), P("结论与后续", "CNH1"), P("当前导出结果证明了导入、证据跨度、分阶段状态机、理论引用字段和人工审核门禁已经产生记录。三个运行停在等待人工审核，另一个运行停在导入阶段；尚未批准任何叙事算子。", "CNBody"), P("若要获得内容敏感的实质分析，需要接入真实的 LLMProvider，并由研究人员逐条核对证据跨度、理论来源和替代解释后再批准。", "CNBody")]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(out)
