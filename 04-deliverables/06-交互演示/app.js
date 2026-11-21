/* Local concept prototype: no account, network, storage, or patient information. */
const names={'01':'入口分流','02':'语音导航','03':'替我说','04':'复述校验','05':'费用说明','06':'家属通知','E1':'我没听清'};
const phrases=['我这两天胸口闷','晚上躺下更明显','我对青霉素过敏','请再说一遍','请写给我看','我需要人扶一下'];
const state={screen:'01',channel:'通用',selected:[],sent:false,sound:false,hold:null,consumed:false,paused:false};
const device=document.querySelector('#device'), message=document.querySelector('#message'), dialog=document.querySelector('#dialog');
function tell(text){message.textContent=text; if(state.sound){speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.lang='zh-CN';utterance.rate=.85;speechSynthesis.speak(utterance);}}
function modal(title,text,actions){document.querySelector('#dialogTitle').textContent=title;document.querySelector('#dialogText').textContent=text;const box=document.querySelector('#dialogButtons');box.replaceChildren();for(const a of actions){const b=document.createElement('button');b.textContent=a.label;b.className=a.primary?'primary':'';b.onclick=()=>{dialog.close();a.run?.();};box.append(b);}if(!dialog.open)dialog.showModal();}
function hit(label,x,y,w,h,run,disabled=false){const b=document.createElement('button');b.className='hit';b.setAttribute('aria-label',label);Object.assign(b.style,{left:x/1024*100+'%',top:y/600*100+'%',width:w/1024*100+'%',height:h/600*100+'%'});b.disabled=disabled;b.onclick=()=>{if(!state.consumed)run();};device.append(b);return b;}
function help(){modal('我帮您叫人','这是人工求助的交互示意，未实际拨号或呼叫。真实使用时应由医院人工服务接入。',[{label:'知道了，继续当前任务',primary:true}]);tell('求助演示已打开，当前任务保留。');}
function holdStart(event){if(event.button!==0)return;const isHelp=event.target.closest('[data-help]');if(state.screen!=='02'&&state.screen!=='01'&&!isHelp)return;clearTimeout(state.hold);const duration=state.screen==='01'&&!isHelp?2000:1500;state.consumed=false;const mark=document.createElement('span');mark.id='hold';mark.textContent='按住中，松手可取消';device.append(mark);state.hold=setTimeout(()=>{state.consumed=true;mark.remove();if(state.screen==='01'&&!isHelp){state.channel='视障';show('02');tell('已进入语音通道。请先松手。往前走十八步，右手边是电梯。');}else help();},duration);}
function holdEnd(){clearTimeout(state.hold);document.querySelector('#hold')?.remove();setTimeout(()=>state.consumed=false,200);}
device.addEventListener('pointerdown',holdStart);window.addEventListener('pointerup',holdEnd);device.addEventListener('pointercancel',holdEnd);
function reset(){state.selected=[];state.sent=false;state.channel='通用';state.paused=false;show('01');tell('已重新开始，请选择使用方式。');}
function consent(){modal('要把小结告诉家人吗？','只发送已发生的就诊节点，不发送位置或轨迹。您可以不发，也可之后关闭通知。',[
 {label:'发给家人',primary:true,run(){state.sent=true;show('06');tell('已按您的选择显示家属通知示例，未实际发送。');}},
 {label:'不发，准备归还',run(){state.sent=false;finish();}}
]);}
function finish(){modal('归还设备并清空本次演示？','清空后回到入口；本次选择不会被保留。这里演示清空反馈，不代表真实后台安全删除已经验证。',[
 {label:'确认归还并清空',primary:true,run(){reset();tell('本次演示选择已清空，下一位可重新开始。');}}, {label:'暂不归还，继续查看'}
]);}
function toggleChip(i){const index=state.selected.indexOf(i);if(index<0)state.selected.push(i);else state.selected.splice(index,1);show('03');tell(state.selected.length?`已选择${state.selected.length}句，可念给医生听。`:'尚未选择短句。');}
function show(key){state.screen=key;device.innerHTML=SCREENS[key];document.querySelectorAll('#nav button').forEach(b=>b.setAttribute('aria-current',String(b.dataset.key===key)));
 if(key==='01'){[['老人自己来','通用','04'],['眼睛看不见','视障','02'],['耳朵听不见','听障','03']].forEach(([label,channel,next],i)=>hit(label,48+320*i,224,288,232,()=>{state.channel=channel;show(next);tell(channel==='视障'?'往前走十八步。右手边是电梯。':`已选择${channel}方式，可随时重新选择。`);}));}
 if(key==='02'){tell('往前走十八步。右手边是电梯。说「再说一遍」可重播，说「等等」暂停，说「到了」继续。');}
 if(key==='03'){
  device.querySelectorAll('svg circle[fill="#0E6E63"],svg path[stroke="#FFFFFF"]').forEach(n=>n.remove());
  const boxes=[...device.querySelectorAll('svg rect')].filter(n=>n.getAttribute('height')==='88');
  boxes.forEach((n,i)=>{n.setAttribute('fill',state.selected.includes(i)?'#DCEAE6':'#FFFFFF');n.setAttribute('stroke',state.selected.includes(i)?'#0E6E63':'#E3DFD7');if(state.selected.includes(i)){const t=document.createElementNS('http\x3a//www.w3.org/2000/svg','text');t.setAttribute('x',Number(n.getAttribute('x'))+264);t.setAttribute('y',Number(n.getAttribute('y'))+28);t.setAttribute('fill','#0E6E63');t.setAttribute('font-size','26');t.textContent='✓';device.querySelector('svg').append(t);}hit(phrases[i],48+(i%3)*320,168+Math.floor(i/3)*112,288,88,()=>toggleChip(i));});
  hit('念给医生听',48,392,396,120,()=>{tell('设备代说示例：'+state.selected.map(i=>phrases[i]).join('。')+'。医生回复以屏幕字幕呈现。');modal('设备代说','已选短句将按选择顺序播放。示例医生回复：先抽血，再做心电图。',[{label:'继续核对医生交代',primary:true,run(){show('04');}},{label:'再选短句'}]);},state.selected.length===0);
 }
 if(key==='04'){hit('对，就是这样',48,396,396,120,()=>{show('05');tell('已确认示例医嘱，请查看费用说明。');});hit('不对，我再说一遍',468,396,396,120,()=>{show('E1');tell('请重新说明，系统不自动猜测。');});}
 if(key==='E1'){['心内','心衰'].forEach((s,i)=>hit(s,176+i*352,184,320,200,()=>{show('04');tell('已记录您选择「'+s+'」，请再次核对示例信息；这不是诊断。');}));hit('都不是，我再说一遍',176,432,672,88,()=>modal('请再说一遍','两个候选均未选择，请重新说明。您也可以求助人工。',[{label:'返回复述校验',primary:true,run(){show('04');}},{label:'人工求助',run:help}]));}
 if(key==='05'){hit('去缴费',48,432,396,88,()=>modal('前往医院缴费','金额为演示数据，实际以医院结算单为准。原型不代扣款、不处理支付。',[{label:'查看本次小结',primary:true,run:consent},{label:'再看看'}]));hit('先不交，我再看看',468,432,396,88,()=>{tell('已保留当前费用说明，未发起支付。');modal('暂不缴费','您可以继续核对费用，或查看小结后归还。',[{label:'继续核对费用'},{label:'查看小结',run:consent}]);});}
 if(key==='06'){tell(state.sent?'家属通知示例：只报节点，不做定位。':'正在查看家属页面设计。尚未同意发送，原型未发送任何通知。');hit('关闭家属通知',598,464,250,88,()=>modal('关闭家属通知','关闭后不再显示新的推送示例，既有就诊任务保留。',[{label:'关闭通知',primary:true,run(){state.sent=false;tell('已关闭通知示例。');}},{label:'继续查看'}]));}
 if(key!=='02'){const b=hit('长按1.5秒求助',888,470,88,88,()=>tell('请按住求助键1.5秒，松手可取消。'));b.dataset.help='true';b.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();help();}};}
}
for(const [key,name] of Object.entries(names)){const b=document.createElement('button');b.textContent=key+' '+name;b.dataset.key=key;b.onclick=()=>{show(key);tell('正在查看'+name+'页面设计。');};document.querySelector('#nav').append(b);}
document.querySelector('#restart').onclick=reset;document.querySelector('#return').onclick=finish;
document.querySelector('#sound').onclick=()=>{state.sound=!state.sound;document.querySelector('#sound').textContent=state.sound?'关闭演示语音':'打开演示语音';document.querySelector('#sound').setAttribute('aria-pressed',state.sound);if(!state.sound)speechSynthesis.cancel();};
function say(){const v=document.querySelector('#voice').value.trim();if(!v)return;if(v.includes('再说一遍')){tell(state.screen==='02'?'往前走十八步。右手边是电梯。':'我复述一遍：二楼抽血、心电图，先抽血。');}else if(v.includes('求助')||v.includes('叫人'))help();else if(v.includes('等等')){state.paused=true;tell('已暂停，请准备好后再继续。');}else if(v==='不发'){state.sent=false;finish();}else if(v==='发'){consent();}else if(v==='不对'){show('E1');tell('请重新说明。');}else if(state.screen==='02'&&['到了','对','好'].includes(v)){show('04');tell('已确认继续，请核对医生交代。');}else if(state.screen==='04'&&['对','好'].includes(v)){show('05');tell('已语音确认示例信息。');}else{tell('没有识别为演示命令；可说「对」「不对」「再说一遍」「等等」「到了」「求助」。');}document.querySelector('#voice').value='';}
document.querySelector('#say').onclick=say;document.querySelector('#voice').onkeydown=e=>{if(e.key==='Enter')say();};show('01');
