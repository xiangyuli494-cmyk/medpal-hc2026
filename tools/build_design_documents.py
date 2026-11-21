"""Build the illustrated design document and four presentation boards.

Usage: python tools/build_design_documents.py [--font PATH] [--qa PATH]
Requires reportlab, PyMuPDF and Pillow. No network access or personal data.
"""
from pathlib import Path
import argparse, io, re, hashlib, json
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
import fitz

ROOT = Path(__file__).resolve().parents[1]
PAPER = '#F6F3EE'; INK = '#14181A'; MUTED = '#61696D'; TEAL = '#0E6E63'; LINE = '#E3DFD7'
SCREENS = [('01','入口分流'),('02','视障语音通道'),('03','替我说'),('04','复述校验'),('05','医保三宫格'),('06','家属端'),('E1','我没听清')]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', default='C:/Windows/Fonts/SourceHanSansCN-Normal.ttf')
    parser.add_argument('--qa', default=str(ROOT/'tmp/pdfs/nonvideo-qa'))
    args=parser.parse_args(); qa=Path(args.qa);qa.mkdir(parents=True,exist_ok=True)
    font=Path(args.font)
    if not font.is_file(): raise FileNotFoundError('Pass --font with an open-source Chinese TrueType font')
    pdfmetrics.registerFont(TTFont('Han',str(font)))
    images={key:ROOT/f'04-deliverables/01-高保真图/小暖_{key}_{name}@2x.png' for key,name in SCREENS}
    missing=[str(p) for p in images.values() if not p.is_file()]
    if missing: raise FileNotFoundError('Missing final screens: '+', '.join(missing))
    flows={}
    for name in ['主流程','三通道','异常降级']:
        source=ROOT/f'04-deliverables/02-流程图/小暖_流程图_{name}.pdf'
        d=fitz.open(source); dest=qa/f'flow-{name}.png'
        d[0].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(dest);flows[name]=dest
    body=ParagraphStyle('body',fontName='Han',fontSize=10.5,leading=17,textColor=colors.HexColor(INK),spaceAfter=10,wordWrap='CJK')
    heading=ParagraphStyle('heading',parent=body,fontSize=22,leading=31,textColor=colors.HexColor(TEAL),spaceAfter=17)
    small=ParagraphStyle('small',parent=body,fontSize=8.5,leading=13,spaceAfter=8,textColor=colors.HexColor(MUTED))
    def para(text,style=body): return Paragraph(escape(text),style)
    W=A4[0]-112
    def picture(path,width=W,caption=''):
        from PIL import Image as PILImage
        im=PILImage.open(path); h=width*im.height/im.width
        flow=Image(str(path),width=width,height=h);flow.hAlign='CENTER'
        return [flow,Spacer(1,7)]+([para(caption,small)] if caption else [])
    def grid(keys,width=W):
        rows=[]
        for key in keys:
            rows.append(picture(images[key],width/len(keys)-7))
        return Table([rows],colWidths=[width/len(keys)]*len(keys),style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
    source=(ROOT/'04-deliverables/05-设计说明/T1-六章统稿-本地审阅.md').read_text(encoding='utf8')
    pages=re.split(r'<!-- page:P\d{2} -->',source)[1:]
    assert len(pages)==12
    story=[]
    for idx,page in enumerate(pages,1):
        lines=page.strip().splitlines(); parsed=[];i=0
        while i<len(lines):
            line=lines[i].strip();i+=1
            if not line or line.startswith('图位'):continue
            if idx==1 and line.startswith('## '):line='## 小暖 · 交互设计说明'
            if idx==1 and line.startswith('本稿由T1整理'):line='本说明包含六章正文、七屏界面与三类交互流程。交付为交互设计概念，真实医疗系统接入、临床有效性与目标用户验证尚未完成。'
            if idx==11 and line.startswith('已有一位编号'):line='已有编号T-1的一次三屏朗读复述记录，涉及02、04、E1。三条复述由采集者判定可理解；年龄、关系及部分条件缺失，记录方法含朗读与候选展示。[S2]'
            if idx==11 and line.startswith('七屏验收共35格'):line='七屏界面与本地概念原型已完成。桌面浏览器16项自动走查覆盖明确确认、纠错、空选禁用、长按、重播、拒绝通知及归还等反馈；记录随内部交付留档。这不是目标用户效果测试，也不证明真实医疗、通知或安全删除能力。'
            if idx==11 and line.startswith('尚未观察到'):line='尚未观察到的性能不写入结果。样本不足与真实行为未测仍是验证限制，不能因七屏图齐全而写成“已验证”。'
            if idx==12 and line.startswith('待替换：'):line='交付范围：七屏PNG、三张流程PDF、交互概念原型、本说明和展示板。目标用户测试、医疗系统接口、语音识别与安全擦除仍待真实实现和验证；视频、承诺签署及校赛提交状态另行确认。'
            if idx==12 and line.startswith('## '):line='## 来源与交付范围'
            if idx==12 and line.startswith('S1：'):line='S1：随附《研究依据摘要》中的12张脱敏原话卡节选；原始材料由研究记录负责人维护。便利样本和未核信息保留，不作统计推断。'
            if idx==12 and line.startswith('S2：'):line='S2：《研究依据摘要》所列一次三屏局部复述记录。年龄和测试条件未齐，不将其写成60岁以上完整可用性验证。'
            if line.startswith('## '):parsed.append(para(line[3:],heading))
            elif line.startswith('|'):
                tablelines=[line]
                while i<len(lines) and lines[i].strip().startswith('|'):
                    tablelines.append(lines[i].strip());i+=1
                rows=[]
                for l in tablelines:
                    cells=[x.strip() for x in l.strip('|').split('|')]
                    if all(re.fullmatch(r'[-: ]+',x or ' ') for x in cells):continue
                    rows.append([para(x,small if rows else ParagraphStyle('th',parent=small,textColor=colors.white)) for x in cells])
                cols=len(rows[0]); widths=[W*.2,W*.34,W*.46] if cols==3 else [W*.32,W*.68]
                table=Table(rows,colWidths=widths,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(TEAL)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor(PAPER),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),5)]));parsed += [table,Spacer(1,12)]
            else:parsed.append(para(line))
        story+=parsed
        if idx==1:story+=picture(images['04'],W,'复述校验：先把记录念回给人听，再由使用者确认或纠错。')
        if idx==2:story+=picture(flows['主流程'],W,'11节点主流程缩略。完整A3流程图随作品单独提供；拒绝通知仍可归还。')
        if idx==3:
            for q in ['卡1：“问人，一般都是问人”——分段指引仍需检验。','卡4：“有，回家都想不起来”——探索医嘱记忆辅助。','卡10：押金与损坏赔付顾虑——借用条件需解释。']:
                box=Table([[para(q,small)]],colWidths=[W]);box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(PAPER)),('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story += [box,Spacer(1,8)]
        if idx==5:story += [grid(['01','02','03']),Spacer(1,8),para('01选择通道 / 02语音引导 / 03文字代说。图中为不同使用方式对照，非一名患者的连续实测。',small)]
        if idx==6:story += [grid(['04','05']),Spacer(1,8),para('04明确确认与纠错；05先给总额与个人支出，再解释明细。完整PNG可单独放大查看。',small)]
        if idx==7:story+=picture(flows['三通道'],W,'01–11全节点 × 三种通道。07进诊室是关键差异；每条通道保留用户拒绝。完整A3另附。')
        if idx==8:
            pair=Table([[picture(flows['异常降级'],W/2-7),picture(images['E1'],W/2-7)]],colWidths=[W/2,W/2],style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
            story += [pair,Spacer(1,8),para('左：异常降级流程缩略，完整A3另附。右：E1候选同等呈现，无默认选择。',small)]
        if idx==9:
            story += [para('呈现 → 确认 → 可拒绝 → 可恢复',heading),para('演示将界面反馈与真实医疗能力分开；不把预设数据当医院实时接口。',small)]
        if idx==10:story+=picture(images['06'],W,'家属端：只报已完成的节点，明确同意后发送，并可关闭；不展示实时定位。')
        if idx<12:story.append(PageBreak())
    report=ROOT/'04-deliverables/05-设计说明/小暖_设计说明.pdf'
    raw=qa/'report-raw.pdf'
    def frame(c,d):
        w,h=A4;c.setFillColor(colors.HexColor(TEAL));c.setFont('Han',8.5);c.drawString(56,h-36,'小暖 / 院内智慧陪诊终端');c.setFillColor(colors.HexColor(MUTED));c.drawRightString(w-56,h-36,'数字媒体设计 · 交互概念')
        c.setStrokeColor(colors.HexColor(LINE));c.line(56,h-46,w-56,h-46);c.setFont('Han',7.5);c.drawString(56,31,'交互概念 / 演示数据 / 不替代医护判断');c.drawRightString(w-56,31,f'{d.page:02} / 12')
    def canvasmaker(*a,**kw):kw['initialFontName']='Han';return Canvas(*a,**kw)
    SimpleDocTemplate(str(raw),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=76,bottomMargin=54,title='小暖_设计说明',author='',creator='').build(story,onFirstPage=frame,onLaterPages=frame,canvasmaker=canvasmaker)
    clean(raw,report,'小暖_设计说明',12)
    boards=ROOT/'04-deliverables/04-展板/小暖_展板.pdf';boards.parent.mkdir(parents=True,exist_ok=True)
    boardraw=qa/'boards-raw.pdf';bw,bh=841*72/25.4,1189*72/25.4
    c=Canvas(str(boardraw),pagesize=(bw,bh),initialFontName='Han');c.setTitle('小暖_展板')
    margin=150; usable=bw-margin*2
    def text(x,y,t,size=34,color=INK):c.setFillColor(colors.HexColor(color));c.setFont('Han',size);c.drawString(x,y,t)
    def wrapped(x,y,t,width,size=34,leading=55,color=INK):
        lines=[];line=''
        for ch in t:
            if pdfmetrics.stringWidth(line+ch,'Han',size)>width:lines.append(line);line=ch
            else:line+=ch
        if line:lines.append(line)
        for line in lines:text(x,y,line,size,color);y-=leading
        return y
    def pic(path,x,top,width):
        from PIL import Image as PILImage
        im=PILImage.open(path);height=width*im.height/im.width
        c.drawImage(str(path),x,top-height,width=width,height=height,mask='auto');return top-height
    def start(n,kicker,title,subtitle):
        c.setFillColor(colors.HexColor(PAPER));c.rect(0,0,bw,bh,fill=1,stroke=0)
        text(margin,bh-150,kicker,29,TEAL);text(margin,bh-290,title,88,INK)
        wrapped(margin,bh-375,subtitle,usable,38,62,MUTED)
        c.setStrokeColor(colors.HexColor(LINE));c.line(margin,130,bw-margin,130)
        text(margin,86,'小暖 · 院内智慧陪诊终端 / 交互设计概念',25,MUTED);text(bw-margin-75,86,f'{n}/4',25,MUTED)
    start(1,'主视觉 / DESIGN OVERVIEW','下一步，小暖陪您走','把当前任务说清楚，把确认权留给人。7寸横屏手持终端，服务台借出，离院归还。')
    y=pic(images['04'],margin,bh-610,usable)
    y-=100;text(margin,y,'从信息，到理解，再到自己确认',58,TEAL);y-=95
    y=wrapped(margin,y,'项目以11个节点组织常规门诊流程，用七张关键页面展示三通道协助。无需先安装应用，界面始终聚焦当前任务。',usable,39,65)-100
    for title,desc in [('看得清','暖纸底、56px主话、统一组件与大热区。'),('说得出','听障使用者点选文字，由设备替其表达。'),('记得住','医生交代被念回、呈现，再由使用者确认。')]:
        text(margin,y,title,50,TEAL);y=wrapped(margin+350,y,desc,usable-350,37,60)-100
    text(margin,250,'界面反馈与数据为模拟；尚未部署于真实医院。',31,MUTED);c.showPage()
    start(2,'三通道 / ACCESSIBLE INTERACTION','同一个任务，三种获取方式','通用大字、视障语音、听障文字代说。模式差异服务于获取信息与表达，不增加重复选择。')
    y=bh-590
    for key,title,desc in [('01','入口分流','一次选择通道，支持重选。长按2秒进入语音通道，松手后再接受后续动作。'),('02','语音引导','完成导航无需点按；说“再说一遍”重播，长按1.5秒求助。设备只指引电梯方位。'),('03','替我说','至少选中一句即可代说；回复用字幕呈现，患者不必依靠听觉获取信息。')]:
        width=1080;bottom=pic(images[key],margin,y,width)
        text(margin+1160,y-50,title,55,TEAL);wrapped(margin+1160,y-145,desc,usable-1160,35,59)
        y=bottom-170
    text(margin,250,'三通道为不同使用方式对照，不是同一患者的连续实测。',31,MUTED);c.showPage()
    start(3,'任务与流程 / TASK FLOW','每一步，都能确认和纠错','复述医嘱、解释金额、拒绝通知、正常归还。系统的不确定需要对用户可见。')
    y=bh-590;gap=70;col=(usable-gap)/2
    for key,title,x,top in [('04','复述确认',margin,y),('05','费用解释',margin+col+gap,y),('E1','不猜，问您',margin,y-900),('06','只报节点，不做定位',margin+col+gap,y-900)]:
        text(x,top,title,43,TEAL);pic(images[key],x,top-65,col)
    y=bh-2520
    for line in ['386 = 253 + 133；费用以医院结算单为准。','通知先问“发 / 不发”，拒绝发送也能归还。','归还后展示清空反馈，不宣称安全擦除已验证。']:
        text(margin,y,line,38,INK);y-=110
    text(margin,250,'主流程 / 三通道 / 六类异常：完整三张A3流程图另附。',31,MUTED);c.showPage()
    start(4,'边界与可行性 / EVIDENCE & LIMITS','辅助就医，不替人做医疗决定','记录能支持到哪里，结论就写到哪里。把设计假设、界面演示与真实能力分开。')
    y=bh-650
    for title,desc in [('已有依据','三位受访者的12张脱敏原话卡，用于提出设计问题，不用于统计推断。'),('验证局限','已有一次三屏局部复述记录；目标视障与听障用户访谈、完整院内试用仍待开展。'),('演示范围','七屏界面、交互概念原型与预设示例数据。页面可演示，不等于医疗系统已接入。'),('工程前提','真实识别、路线核对、医院授权接口、加密与删除效果，需要另外实现并测试。'),('控制权','确认、拒绝和求助均有出口；通知须明确同意，不因沉默自动开启。')]:
        text(margin,y,title,52,TEAL);y=wrapped(margin,y-90,desc,usable,39,66)-125
    text(margin,340,'来源：脱敏访谈记录、信息架构与交互流程、七屏清单。',29,MUTED)
    text(margin,270,'详细证据范围与来源编号见随附《小暖_设计说明》第3–4、11–12页。',29,MUTED);c.showPage();c.save()
    clean(boardraw,boards,'小暖_展板',4)
    for label,path in [('report',report),('board',boards)]:
        doc=fitz.open(path)
        for i,page in enumerate(doc):
            text_content=page.get_text();assert '\ufffd' not in text_content
            scale=min(1.5,1400/page.rect.width)
            page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).save(qa/f'{label}-{i+1:02}.png')
            for word in page.get_text('words'):
                assert word[0]>=0 and word[1]>=0 and word[2]<=page.rect.width+.5 and word[3]<=page.rect.height+.5,(path,i,word)
        print(path,len(doc),'pages',path.stat().st_size,'bytes')
    (qa/'document-build.json').write_text(json.dumps({'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'boards_sha256':hashlib.sha256(boards.read_bytes()).hexdigest(),'screen_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in images.items()},'limitations':['真实目标用户测试待完成','医疗后台与语音能力未部署','原创承诺与学校提交需本人确认']},ensure_ascii=False,indent=2),encoding='utf8')

def clean(source,target,title,pages):
    doc=fitz.open(source);assert len(doc)==pages,(target,len(doc),pages)
    doc.set_metadata({'title':title,'author':'','creator':'','producer':'','subject':'交互设计概念；真实用户验证与工程部署待完成'})
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(doc.tobytes(garbage=4,deflate=True));doc.close()

if __name__=='__main__':main()
