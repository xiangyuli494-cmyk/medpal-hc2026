"""Render the 92-second narrated interaction concept film from supplied clips."""
from pathlib import Path
import argparse,bisect,json,math,re,subprocess,wave
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--media-root',required=True);parser.add_argument('--font',default='C:/Windows/Fonts/SourceHanSansCN-Normal.ttf');parser.add_argument('--render',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(args.output).resolve();WORK=OUT/'work'
MEDIA=Path(args.media_root).resolve()
W,H,FPS,DURATION=1920,1080,24,92
FONT=args.font
PAPER='#F6F3EE';INK='#14181A';TEAL='#0E6E63';MUTED='#61696D'
SOURCE={1:'1795003611715..mp4',2:'1795179370073.mp4',3:'video_20261118_200321.mp4',4:'video_20261118_195950.mp4',5:'1795179380873.mp4',6:'1795179367599.mp4',7:'video_20261118_195910.mp4',8:'video_20261118_195741.mp4'}
CHAPTERS=[(0,'01 / 一个人就医','下一步，该往哪走？'),(8,'02 / 从借用开始','小暖 · 院内智慧陪诊终端'),(18,'03 / 视障语音通道','看不见，也能听到下一步'),(29,'04 / 听障文字通道','想说的话，设备替您表达'),(42,'05 / 复述校验','先复述，再由您确认'),(52,'06 / 没听清时','不猜答案，请您再确认'),(59,'07 / 费用说明','先给结论，再看明细'),(71,'08 / 家属通知','先问同意，只报节点'),(82,'09 / 归还与结束','下一位，从新的页面开始')]
# start, end, type, asset, source-in, speed
SHOTS=[(0,3.8,'video',8,0,1),(3.8,8,'video',7,0,1),(8,12.8,'video',6,.1,.96),(12.8,18,'ui','01',0,1),(18,20,'video',5,0,1),(20,22,'video',3,0,1),(22,29,'ui','02',0,1),(29,31,'video',4,0,1),(31,31.9,'ui','03-empty',0,1),(31.9,32.8,'ui','03-one',0,1),(32.8,38.3,'ui','03-two',0,1),(38.3,42,'ui','03-reply',0,1),(42,44,'video',1,.2,1),(44,52,'ui','04',0,1),(52,59,'ui','E1',0,1),(59,71,'ui','05',0,1),(71,74.2,'ui','consent',0,1),(74.2,82,'ui','06',0,1),(82,86,'video',2,0,.98),(86,88.5,'ui','reset',0,1),(88.5,92,'end','end',0,1)]
FONTS={n:ImageFont.truetype(FONT,n) for n in [20,22,24,26,28,32,38,42,44,52,62,72,88,156]}
CAPS=json.loads((WORK/'narration.json').read_text(encoding='utf8'))

def normalize(t):return ''.join(c for c in t if c.isalnum())
def captions():
    result=[]
    for a in CAPS:
        timings=json.loads((WORK/f'voice-{a["id"]}.json').read_text(encoding='utf8'));char_times=[]
        for word in timings:
            chars=normalize(word['text'])
            for i,_ in enumerate(chars):char_times.append((word['start']+word['duration']*i/max(1,len(chars)),word['start']+word['duration']*(i+1)/max(1,len(chars))))
        assert len(char_times)==len(normalize(a['text'])),a
        chunks=[]
        for sentence in re.findall(r'[^。！？；]+[。！？；]?',a['text']):
            if len(sentence)<=22:chunks.append(sentence);continue
            parts=re.findall(r'[^，；]+[，；]?',sentence);current=''
            for part in parts:
                if current and len(current+part)>22:chunks.append(current);current=''
                current+=part
            if current:chunks.append(current)
        pos=0
        for chunk in chunks:
            count=len(normalize(chunk));start=a['start']+char_times[pos][0]/a['speed'];end=a['start']+char_times[pos+count-1][1]/a['speed']+.20
            result.append({'start':start,'end':min(end,a['start']+a['slot']),'text':chunk.strip('，；。'),'speaker':'设备代说' if a['id']=='04b' else '解说'})
            pos+=count
    result.sort(key=lambda v:v['start'])
    # Earlier captions have display priority; match SRT intervals to that behavior.
    for i in range(1,len(result)):result[i]['start']=max(result[i]['start'],result[i-1]['end'])
    return result
SUBS=captions()

def text(d,xy,value,size=42,fill=INK,anchor=None,stroke=0):
    d.text(xy,value,font=FONTS[size],fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=fill)

def base_ui():
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    d.ellipse((-530,-430,240,340),fill='#E8EDE7');d.ellipse((1660,750,2190,1280),fill='#EEE8DD')
    # Device framing is for video presentation only; formal PNGs remain pure UI.
    shadow=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((303,177,1617,958),32,fill=(20,24,26,34));shadow=shadow.filter(ImageFilter.GaussianBlur(15));im=Image.alpha_composite(im.convert('RGBA'),shadow).convert('RGB')
    d=ImageDraw.Draw(im);d.rounded_rectangle((304,174,1616,956),30,fill='#23322E',outline='#B1BBB3',width=2)
    return im

UI={}
for key in ['01','02','04','05','E1']:
    p=next((ROOT/'04-deliverables/01-高保真图').glob(f'小暖_{key}_*.png'));im=base_ui();im.paste(Image.open(p).convert('RGB').resize((1280,750),Image.Resampling.LANCZOS),(320,190));UI[key]=im
for key in ['03-empty','03-one','03-two','03-reply','consent','06','reset']:
    im=base_ui();im.paste(Image.open(WORK/f'ui-{key}.png').convert('RGB').resize((1280,750),Image.Resampling.LANCZOS),(320,190));UI[key]=im

END=Image.new('RGB',(W,H),PAPER);ed=ImageDraw.Draw(END)
ed.ellipse((-400,-500,800,700),fill='#E4ECE7');ed.ellipse((1500,550,2350,1400),fill='#EEE8DD')
text(ed,(960,320),'小暖',156,TEAL,'mm',1);text(ed,(960,480),'把下一步，说清楚。',62,INK,'mm')
for x,label in [(620,'看得清'),(960,'说得出'),(1300,'记得住')]:
    ed.rounded_rectangle((x-125,590,x+125,662),36,fill='#DCEAE6');text(ed,(x,626),label,32,TEAL,'mm')
text(ed,(960,775),'交互概念演示 · 场景为情境示意',26,MUTED,'mm')
text(ed,(960,825),'界面、通知及清空反馈为模拟 · 不替代医护判断',26,MUTED,'mm')

class Video:
    def __init__(self):self.caps={};self.frames={};self.indices={}
    def get(self,key,t):
        if key not in self.caps:self.caps[key]=cv2.VideoCapture(str(MEDIA/SOURCE[key]));self.indices[key]=-1
        cap=self.caps[key];idx=int(t*cap.get(cv2.CAP_PROP_FPS))
        if idx!=self.indices[key]:
            if idx!=self.indices[key]+1:cap.set(cv2.CAP_PROP_POS_FRAMES,idx)
            ok,frame=cap.read()
            if not ok:frame=self.frames[key]
            else:self.frames[key]=frame
            self.indices[key]=idx
        frame=self.frames[key];h,w=frame.shape[:2];crop=int(w*9/16);frame=frame[(h-crop)//2:(h-crop)//2+crop]
        frame=cv2.resize(frame,(W,H),interpolation=cv2.INTER_CUBIC)
        return Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
    def close(self):
        for c in self.caps.values():c.release()
VIDEO=Video()

gradient=Image.new('RGBA',(W,H));ga=np.zeros((H,W,4),dtype=np.uint8)
ga[:240,:,3]=np.linspace(135,0,240).astype(np.uint8)[:,None]
ga[840:,:,3]=np.linspace(0,120,240).astype(np.uint8)[:,None]
gradient=Image.fromarray(ga)

def raw_frame(shot,t):
    start,end,kind,key,sourcein,speed=shot
    if kind=='video':return VIDEO.get(key,max(0,sourcein+(t-start)*speed))
    if kind=='end':return END.copy()
    return UI[key].copy()

def ring(d,x,y,t,start,length=1.1):
    phase=(t-start)/length
    if 0<=phase<=1:
        px=320+x*1.25;py=190+y*1.25;r=15+24*phase
        d.ellipse((px-r,py-r,px+r,py+r),outline=(14,110,99,int(230*(1-phase))),width=4)
        d.ellipse((px-8,py-8,px+8,py+8),fill=(14,110,99,220),outline='white',width=2)

def frame(t):
    idx=max(i for i,s in enumerate(SHOTS) if s[0]<=t);shot=SHOTS[idx];im=raw_frame(shot,t)
    # Short dissolves soften shot changes while preserving the actual source motions.
    delta=t-shot[0]
    if idx>0 and delta<.28:
        previous=raw_frame(SHOTS[idx-1],SHOTS[idx-1][1]-.05)
        im=Image.blend(previous,im,min(1,delta/.28))
    kind=shot[2];overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
    if kind=='video':im=Image.alpha_composite(im.convert('RGBA'),gradient).convert('RGB')
    chapter=max(i for i,v in enumerate(CHAPTERS) if v[0]<=t)
    _,kicker,title=CHAPTERS[chapter]
    if kind!='end':
        color='white' if kind=='video' else INK
        text(d,(82,36),kicker,24,'#A6E1D3' if kind=='video' else TEAL)
        text(d,(78,77),title,44,color,stroke=1)
        d.rounded_rectangle((1452,34,1838,80),23,fill=(10,31,27,200) if kind=='video' else (220,234,230,255))
        text(d,(1645,57),'交互概念演示 · 模拟数据',22,'white' if kind=='video' else TEAL,'mm')
        if 18<=t<42:text(d,(1835,114),'不同使用方式对照 · 非连续实测',22,'white' if kind=='video' else MUTED,'ra')
    if 0<=t<8:
        # Opening caption stays on clear negative space instead of covering the person.
        text(d,(84,272),'一个人来看病',62,'white',stroke=1)
        text(d,(85,371),'最难的，常常是下一步。',38,'#F2F3EE')
    if shot[2]=='ui':
        key=shot[3]
        if key=='01':
            for x,st in [(192,13.5),(512,14.9),(832,16.3)]:ring(d,x,340,t,st)
        if key=='02':
            # Animate the six bars already defined by the approved screen design.
            d.rectangle((320+432*1.25,190+140*1.25,320+592*1.25,190+248*1.25),fill='#06090A')
            for j in range(6):
                h=28+62*(.5+.5*math.sin(t*6+j*.9));x=320+(442+j*26)*1.25;y=190+(244-h)*1.25
                d.rounded_rectangle((x,y,x+12.5,190+244*1.25),6,fill='#5FD3B8')
        if key.startswith('03'):
            ring(d,190,212,t,31.6);ring(d,510,212,t,32.4);ring(d,245,452,t,33.4)
        if key=='04':ring(d,246,455,t,45.5);ring(d,665,455,t,47.0)
        if key=='E1':ring(d,512,476,t,56.2)
        if key=='05':
            for x,st in [(48,62),(368,64.0),(688,66.2)]:
                if st<=t<st+1.8:
                    d.rounded_rectangle((320+x*1.25-5,190+176*1.25-5,320+(x+288)*1.25+5,190+320*1.25+5),28,outline='#0E6E63',width=4)
        if key=='consent':ring(d,350,380,t,73.3)
        if key=='06' and t>=79:
            d.rounded_rectangle((320+598*1.25-5,190+464*1.25-5,320+848*1.25+5,190+552*1.25+5),22,outline='#0E6E63',width=4)
        if key=='reset':
            d.rounded_rectangle((66,744,282,934),24,fill='#0E6E63')
            for y,label in [(784,'演示反馈'),(842,'本次选择'),(895,'已清空')]:text(d,(174,y),label,28,'white','mm')
    # Narration subtitle strip is consistently outside the displayed device UI.
    d.rectangle((0,976,W,H),fill=(13,31,27,245))
    text(d,(76,1026),f'{chapter+1:02} / 09',22,'#A6C0B7','lm')
    active=next((s for s in SUBS if s['start']<=t<s['end']),None)
    if active:
        text(d,(960,1025),active['text'],42,'white','mm')
        if active['speaker']=='设备代说':text(d,(1828,1025),'设备代说',22,'#8ED8C4','rm')
    d.rectangle((0,1076,W*t/DURATION,H),fill='#5FD3B8')
    im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
    if t<.35:im=Image.blend(Image.new('RGB',(W,H),'black'),im,t/.35)
    if t>DURATION-.35:im=Image.blend(im,Image.new('RGB',(W,H),'black'),(t-DURATION+.35)/.35)
    return im

def audio():
    rate=48000;length=int(DURATION*rate);voice_mix=np.zeros(length,dtype=np.float32)
    for a in CAPS:
        src=WORK/f'voice-{a["id"]}.mp3'
        cmd=['ffmpeg','-v','error','-i',str(src),'-af',f'atempo={a["speed"]:.6f},loudnorm=I=-17:TP=-2:LRA=7','-f','f32le','-ar',str(rate),'-ac','1','pipe:1']
        samples=np.frombuffer(subprocess.check_output(cmd),dtype='<f4');start=int(a['start']*rate);stop=min(length,start+len(samples));voice_mix[start:stop]+=samples[:stop-start]
    # Original, quiet synthesized pad; no third-party music recording is used.
    music=np.zeros(length,dtype=np.float32);chords=[[130.8128,164.8138,195.9977],[110,130.8128,164.8138],[87.3071,110,130.8128],[97.9989,123.4708,146.8324]]
    for i,start in enumerate(np.arange(0,DURATION,6)):
        n=min(int(7*rate),length-int(start*rate));t=np.arange(n)/rate;env=np.minimum(t/1.5,1)*np.minimum((n/rate-t)/2,1)
        sig=sum(np.sin(2*np.pi*f*t)+.14*np.sin(2*np.pi*2*f*t) for f in chords[i%4])/3
        music[int(start*rate):int(start*rate)+n]+=(sig*env*.009).astype(np.float32)
    music[:rate]*=np.linspace(0,1,rate);music[-2*rate:]*=np.linspace(1,0,2*rate)
    final=np.clip(voice_mix+music,-.95,.95);stereo=np.column_stack([final,final]);pcm=(stereo*32767).astype('<i2')
    with wave.open(str(OUT/'小暖_完整配音.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
    with wave.open(str(WORK/'narration-only.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes((np.clip(voice_mix,-.95,.95)*32767).astype('<i2').tobytes())
    print('Audio mix ready.',flush=True)

def srt_time(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def metadata():
    (OUT/'小暖_字幕.srt').write_text('\n\n'.join(f'{i}\n{srt_time(s["start"])} --> {srt_time(s["end"])}\n{s["text"]}' for i,s in enumerate(SUBS,1))+'\n',encoding='utf8')
    (OUT/'小暖_配音稿.txt').write_text('\n\n'.join(f'{a["start"]:.1f}秒 / '+('设备代说' if a['id']=='04b' else '解说')+'\n'+a['text'] for a in CAPS),encoding='utf8')
    (WORK/'timeline.json').write_text(json.dumps({'duration':DURATION,'fps':FPS,'shots':SHOTS,'chapters':CHAPTERS,'captions':SUBS},ensure_ascii=False,indent=2),encoding='utf8')

def preview():
    times=[2,9,15,24,31.4,35.5,39.8,46,54,64,72.4,77,84,87,90.5]
    canvas=Image.new('RGB',(1920,4*310),'#DDD8CF');d=ImageDraw.Draw(canvas)
    for i,t in enumerate(times):
        im=frame(t);im.save(WORK/f'preview-{t:.1f}.jpg',quality=92)
        im.thumbnail((480,270));x=i%4*480;y=i//4*310;canvas.paste(im,(x,y+32));text(d,(x+12,y+3),f'{t:.1f}s',20)
    canvas.save(OUT/'小暖_视频分镜预览.jpg',quality=92);print('Preview contact sheet ready.',flush=True)

def render():
    target=OUT/'小暖_演示_配音版.mp4'
    log=(WORK/'ffmpeg-render.log').open('w',encoding='utf8')
    cmd=['ffmpeg','-y','-hide_banner','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(OUT/'小暖_完整配音.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-profile:v','high','-level','4.1','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-map_metadata','-1','-t',str(DURATION),str(target)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
    try:
        for i in range(DURATION*FPS):
            process.stdin.write(frame(i/FPS).tobytes())
            if i%240==0:print(f'Rendered {i/FPS:.0f}/{DURATION}s',flush=True)
        process.stdin.close();code=process.wait();assert code==0,code
    finally:
        VIDEO.close();log.close()
        if process.poll() is None:process.terminate()
    print(str(target),flush=True)

if __name__=='__main__':
    metadata();audio();preview()
    if args.render:render()
