"""Build the seven 1024x600 concept screens and the local prototype assets."""
from pathlib import Path
from html import escape
import json, re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'04-deliverables/01-高保真图'
DEMO=ROOT/'04-deliverables/06-交互演示'
NAMES={'01':'入口分流','02':'视障语音通道','03':'替我说','04':'复述校验','05':'医保三宫格','06':'家属端','E1':'我没听清'}
PAPER='#F6F3EE'; INK='#14181A'; MUTED='#61696D'; TEAL='#0E6E63'; LINE='#E3DFD7'
def text(x,y,s,size=26,color=INK,weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>'
def rect(x,y,w,h,fill='white',rx=20,stroke=LINE):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def button(x,y,w,label,primary=True,h=120):
    return rect(x,y,w,h,TEAL if primary else PAPER,16,TEAL)+text(x+w/2,y+h/2+9,label,26,'white' if primary else TEAL,600,'middle')
def help_key():
    return '<circle cx="932" cy="514" r="44" fill="#B5392F"/>'+text(932,522,'求助',22,'white',700,'middle')
def shell(title,body,footer='',status=True,help=True):
    head='<svg xmlns="http&#58;//www.w3.org/2000/svg" width="1024" height="600" viewBox="0 0 1024 600" font-family="Source Han Sans CN, Noto Sans SC, Microsoft YaHei, sans-serif">'+f'<title>{title}</title>'+rect(0,0,1024,600,PAPER,0,PAPER)
    if status:head+='<circle cx="52" cy="56" r="4" fill="#61696D"/>'+text(66,62,'已开机 · 门诊大厅',18,MUTED)+text(976,62,'20:51 · 已联网',18,MUTED,anchor='end')+'<path d="M48 84H976" stroke="#E3DFD7"/>'
    return head+body+(text(48,552,footer,22,MUTED) if footer else '')+(help_key() if help else '')+'</svg>'

def build():
    OUT.mkdir(parents=True,exist_ok=True);DEMO.mkdir(parents=True,exist_ok=True)
    screens={}
    for key in ['01','02','03','04']:
        p=ROOT/f'02-design/参考-高保真草稿/{key}-{NAMES[key]}.svg'
        s=p.read_text(encoding='utf8').replace("'Noto Sans SC', 'Microsoft YaHei', sans-serif","'Source Han Sans CN', 'Noto Sans SC', 'Microsoft YaHei', sans-serif")
        if key=='03':s=s.replace('stroke-width="2.5"','stroke-width="1.25"')
        screens[key]=s
    body=text(48,142,'这 386 块，医保帮您出了 253 块',40,weight=700)
    for x,label,value in [(48,'总共',386),(368,'医保出',253),(688,'自己掏',133)]:
        body+=rect(x,176,288,144,'#DCEAE6' if value==253 else 'white',20,TEAL if value==253 else LINE)
        body+=text(x+24,217,label,22,MUTED)+text(x+24,291,str(value),56,INK,700)+text(x+177,287,'元',22,MUTED)
    body+=rect(48,334,928,48,'#F8E9D6',12,'#F8E9D6')+text(72,368,'先看结论，再看明细；您只需付 133 元。',26)
    body+=text(48,416,'甲类 153 · 乙类 125（您付 25）· 丙类 108（您全付）',22,MUTED)
    body+=button(48,432,396,'去缴费',h=88)+button(468,432,396,'先不交，我再看看',False,h=88)
    screens['05']=shell('05 医保三宫格',body,'以医院结算单为准。')
    body=text(48,150,'她一个人来的',40,weight=700)+text(48,202,'每一步，我都放心',40,weight=700)
    for y,title,desc in [(280,'只报节点，不做定位','告知到院、检查完成和医生交代。'),(365,'由本人同意后发送','发送前可选「发」或「不发」。'),(450,'随时可以关闭','不显示路线、轨迹或实时位置。')]:
        body+='<circle cx="58" cy="'+str(y-8)+'" r="5" fill="#0E6E63"/>'+text(80,y,title,26,weight=600)+text(80,y+34,desc,22,MUTED)
    body+=rect(578,112,398,336,'white',28)+text(600,149,'家属通知 · 示例',22,MUTED)
    for y,time,title,desc in [(180,'09:10','已到院','已到门诊大厅，准备就诊。'),(264,'09:40','医生交代','二楼：先抽血，再做心电图。'),(348,'10:20','检查已完成','心电图已完成。')]:
        body+=rect(598,y,358,74,PAPER,12,PAPER)+f'<circle cx="616" cy="{y+24}" r="4" fill="#2C7A52"/>'+text(630,y+30,title,22,weight=600)+text(940,y+28,time,18,MUTED,anchor='end')+text(614,y+58,desc,22,MUTED)
    # Distinguish receipt of a summary from a real-time tracking service.
    body+=button(598,464,250,'关闭通知',False,h=88)
    screens['06']=shell('06 家属端',body,'微信服务通知，不装 App。')
    body=text(48,150,'我没听清，您说的是哪个？',40,weight=700)
    for x,word,pinyin in [(176,'心内','xīn nèi'),(528,'心衰','xīn shuāi')]:
        body+=rect(x,184,320,200)+text(x+160,286,word,56,weight=700,anchor='middle')+text(x+160,339,pinyin,22,MUTED,anchor='middle')
    body+=text(176,416,'识别置信度 0.41 · 我不猜，问您。',22,TEAL)
    body+=button(176,432,672,'都不是，我再说一遍',False,h=88)
    screens['E1']=shell('E1 我没听清',body,'您慢慢说，我在听。')
    # The family-page headline is descriptive copy, not a live location promise.
    for key,s in screens.items():
        assert '\ufffd' not in s
    (DEMO/'screens.js').write_text('window.SCREENS='+json.dumps(screens,ensure_ascii=False)+';\n',encoding='utf8')
    return screens

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');args=parser.parse_args()
    screens=build()
    if args.render:
        from playwright.sync_api import sync_playwright
        from PIL import Image
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1024,'height':600},device_scale_factor=2)
            for key,s in screens.items():
                page.set_content('<meta charset="utf-8"><style>html,body{margin:0;width:1024px;height:600px;overflow:hidden}</style>'+s)
                page.evaluate('document.fonts.ready')
                dest=OUT/f'小暖_{key}_{NAMES[key]}@2x.png';page.screenshot(path=str(dest))
                with Image.open(dest) as im:
                    clean=Image.new('RGB',im.size);clean.paste(im.convert('RGB'));clean.save(dest,format='PNG')
                assert Image.open(dest).size==(2048,1200)
            browser.close()
        print('Exported 7 PNG screens at 2048x1200 without image metadata.')
