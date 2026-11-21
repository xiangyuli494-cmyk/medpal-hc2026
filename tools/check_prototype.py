from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect

import argparse
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8768/');parser.add_argument('--qa',required=True);args=parser.parse_args()
out=Path(args.qa);out.mkdir(exist_ok=True,parents=True)
checks=[]
def passed(name): checks.append(name)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':1100})
    errors=[]; external=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:external.append(r.url) if not r.url.startswith(args.url) else None)
    page.goto(args.url);page.evaluate('document.fonts.ready')
    def route(key):
        page.locator('#nav button[data-key="'+key+'"]').click()
    def screen(key):
        expect(page.locator('#nav button[data-key="'+key+'"]')).to_have_attribute('aria-current','true')
    def hit(label):return page.locator('#device').get_by_role('button',name=label,exact=True)
    def say(v):
        page.locator('#voice').fill(v);page.locator('#say').click()
    def hold(x,y,ms):
        b=page.locator('#device').bounding_box();page.mouse.move(b['x']+x/1024*b['width'],b['y']+y/600*b['height']);page.mouse.down();page.wait_for_timeout(ms);page.mouse.up();page.wait_for_timeout(250)
    screen('01');hit('老人自己来').click();screen('04');passed('入口单击进入通用通道')
    say('不太对');screen('04');passed('含糊确认不触发确认跳转')
    hit('不对，我再说一遍').click();screen('E1')
    assert page.locator('#device svg rect[fill="#DCEAE6"]').count()==0
    hit('都不是，我再说一遍').click();expect(page.locator('#dialog')).to_be_visible()
    page.get_by_role('button',name='返回复述校验',exact=True).click();screen('04');passed('异常候选无默认选中且支持均否定')
    route('E1');hit('心内').click();screen('04');expect(page.locator('#message')).to_contain_text('心内');passed('候选选择提供反馈并回到核对')
    hit('对，就是这样').click();screen('05');passed('明确确认后进入费用说明')
    hit('去缴费').click();expect(page.locator('#dialogText')).to_contain_text('不代扣款')
    page.get_by_role('button',name='查看本次小结',exact=True).click();expect(page.locator('#dialogTitle')).to_have_text('要把小结告诉家人吗？')
    page.wait_for_timeout(700);assert page.evaluate('state.sent') is False
    page.get_by_role('button',name='不发，准备归还',exact=True).click()
    page.get_by_role('button',name='确认归还并清空',exact=True).click();screen('01');assert page.evaluate('state.sent') is False;passed('发送需明确同意，拒绝后可归还')
    hit('耳朵听不见').click();screen('03');expect(hit('念给医生听')).to_be_disabled()
    hit('我对青霉素过敏').click();hit('我这两天胸口闷').click();assert page.evaluate('state.selected')==[2,0]
    hit('我对青霉素过敏').click();assert page.evaluate('state.selected')==[0]
    hit('我这两天胸口闷').click();expect(hit('念给医生听')).to_be_disabled();passed('替我说支持空选禁用、多选顺序和取消')
    hit('请写给我看').click();hit('念给医生听').click();expect(page.locator('#message')).to_contain_text('请写给我看')
    page.get_by_role('button',name='继续核对医生交代',exact=True).click();screen('04');passed('设备代说示例和文字回复入口连通')
    hit('对，就是这样').click();hit('先不交，我再看看').click()
    page.get_by_role('button',name='查看小结',exact=True).click();page.get_by_role('button',name='发给家人',exact=True).click();screen('06');assert page.evaluate('state.sent') is True
    expect(page.locator('#message')).to_contain_text('未实际发送')
    hit('关闭家属通知').click();page.get_by_role('button',name='关闭通知',exact=True).click();assert page.evaluate('state.sent') is False;screen('06');passed('同意后仅显示通知示例，随时可关闭')
    page.locator('#return').click();page.get_by_role('button',name='确认归还并清空',exact=True).click()
    assert page.evaluate('state.selected')==[];screen('01');passed('归还后清空当前内存选择并回入口')
    hold(150,190,600);screen('01')
    hold(150,250,2150);screen('02');expect(page.locator('#dialog')).not_to_be_visible();passed('入口空白短按不触发长按，磁贴长按2秒进入语音')
    assert page.locator('#device [data-help]').count()==0
    say('再说一遍');screen('02');expect(page.locator('#dialog')).not_to_be_visible();expect(page.locator('#message')).to_contain_text('十八步')
    say('等等');assert page.evaluate('state.paused') is True
    hold(150,250,1650);expect(page.locator('#dialog')).to_be_visible()
    page.get_by_role('button',name='知道了，继续当前任务',exact=True).click();screen('02');passed('语音通道说话重播、暂停及整屏长按求助')
    say('到了');screen('04');say('好');screen('05');passed('语音明确命令可推进核对和费用说明')
    hold(200,200,1650);expect(page.locator('#dialog')).not_to_be_visible()
    hold(932,514,1650);expect(page.locator('#dialog')).to_be_visible()
    page.get_by_role('button',name='知道了，继续当前任务',exact=True).click();screen('05');passed('其他通道只用求助键长按，保留当前任务')
    route('01');page.screenshot(path=str(out/'原型入口.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    passed('390px窄屏无横向溢出；设备屏按比例缩放')
    assert not errors,errors;assert not external,external;passed('无脚本错误、无外部网络请求')
    browser.close()
(out/'原型实测.json').write_text(json.dumps({'browser':'Microsoft Edge / Playwright headless','checks':checks,'limitations':['不是目标用户测试','没有真实ASR、通知、支付、医院接口','没有验证真实后台安全清除','音频输出受浏览器语音包影响，未听觉实测']},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'passed':len(checks),'checks':checks},ensure_ascii=False,indent=2))
