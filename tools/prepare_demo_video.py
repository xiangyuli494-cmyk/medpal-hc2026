from pathlib import Path
import sys,asyncio,json,re,subprocess
from playwright.sync_api import sync_playwright

import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--proxy');parser.add_argument('--screens',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(args.output).resolve();WORK=OUT/'work';WORK.mkdir(exist_ok=True,parents=True)
LINES=[
 ('01',.35,7.4,'一个人来医院，最怕不知道下一步往哪走。','zh-CN-XiaoxiaoNeural'),
 ('02',8.3,9.3,'从服务台借一台小暖，不用先装应用。开机后，选一种适合自己的方式。','zh-CN-XiaoxiaoNeural'),
 ('03',18.3,10.3,'眼睛看不见，就全程用说的。往前走十八步，右手边是电梯。','zh-CN-XiaoxiaoNeural'),
 ('04a',29.2,4.2,'耳朵听不见，点选短句，也能表达。','zh-CN-XiaoxiaoNeural'),
 ('04b',33.7,4.7,'我这两天胸口闷，晚上躺下更明显。','zh-CN-YunxiNeural'),
 ('04c',38.8,2.9,'医生回复，再用文字呈现。','zh-CN-XiaoxiaoNeural'),
 ('05',42.3,9.3,'医生交代的事，再复述一遍。对，就确认；不对，就重说。决定权，留给您。','zh-CN-XiaoxiaoNeural'),
 ('06',52.2,6.5,'没听清，就给出同等候选。不猜，也能重说。','zh-CN-XiaoxiaoNeural'),
 ('07',59.2,11.5,'费用先给结论，再看明细。总共三百八十六元，医保出二百五十三元，自己付一百三十三元。','zh-CN-XiaoxiaoNeural'),
 ('08',71.2,10.4,'告诉家人之前，先问您同不同意。只报就诊节点，不报位置；不想发，也能正常归还。','zh-CN-XiaoxiaoNeural'),
 ('09',82.3,9.1,'归还设备，结束这次使用。下一位，从新的页面开始。小暖，让每一步，都更明白。','zh-CN-XiaoxiaoNeural'),
]

async def voices():
    import edge_tts
    semaphore=asyncio.Semaphore(3)
    async def one(line):
        key,start,slot,text,voice=line;dest=WORK/f'voice-{key}.mp3';bound=WORK/f'voice-{key}.json'
        async with semaphore:
            if not dest.exists() or not bound.exists():
                timings=[]
                for attempt in range(3):
                    try:
                        talk=edge_tts.Communicate(text,voice,rate='+6%' if voice.endswith('XiaoxiaoNeural') else '+0%',boundary='WordBoundary',proxy=args.proxy)
                        with dest.open('wb') as f:
                            async for chunk in talk.stream():
                                if chunk['type']=='audio':f.write(chunk['data'])
                                elif chunk['type']=='WordBoundary':timings.append({'text':chunk['text'],'start':chunk['offset']/1e7,'duration':chunk['duration']/1e7})
                        bound.write_text(json.dumps(timings,ensure_ascii=False,indent=2),encoding='utf8');break
                    except Exception:
                        if attempt==2:raise
                        timings=[];await asyncio.sleep(2)
            duration=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(dest)]))['format']['duration'])
            speed=max(1,duration/slot)
            result={'id':key,'start':start,'slot':slot,'text':text,'voice':voice,'source_duration':duration,'speed':speed}
            print(json.dumps(result,ensure_ascii=False),flush=True);return result
    result=await asyncio.gather(*(one(l) for l in LINES))
    (WORK/'narration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')

def screens():
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1024,'height':600},device_scale_factor=2)
        page.goto((ROOT/'04-deliverables/06-交互演示/index.html').as_uri())
        page.add_style_tag(content='header,nav,.controls,#message,.hint{display:none!important}html,body{margin:0;padding:0;width:1024px;height:600px;overflow:hidden}main{margin:0;padding:0;max-width:none}.device{position:fixed;inset:0;width:1024px;height:600px}dialog{margin:auto}dialog h2{font-size:28px}dialog p{font-size:22px}dialog button{font-size:22px}')
        page.evaluate('document.fonts.ready')
        def shot(name):page.screenshot(path=str(WORK/f'ui-{name}.png'))
        page.evaluate("show('03')");shot('03-empty')
        page.evaluate('toggleChip(0)');shot('03-one')
        page.evaluate('toggleChip(1)');shot('03-two')
        page.get_by_role('button',name='念给医生听',exact=True).click();shot('03-reply')
        page.evaluate("dialog.close();show('05');consent()");shot('consent')
        page.get_by_role('button',name='发给家人',exact=True).click();shot('06')
        page.evaluate('finish()');shot('return')
        page.get_by_role('button',name='确认归还并清空',exact=True).click();shot('reset')
        assert page.evaluate('state.selected.length===0 && state.sent===false')
        browser.close();print('Captured 8 prototype states.',flush=True)

if __name__=='__main__':
    if args.screens:screens()
    else:asyncio.run(voices())
