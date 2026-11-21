"""Package only reviewed non-video artifacts. Usage: --output <new folder>."""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
    dest=Path(args.output).resolve()
    if dest.exists() or dest.with_suffix('.zip').exists():
        raise FileExistsError('Use a new output folder; existing deliverables are never overwritten.')
    sources=[]
    for path in sorted((ROOT/'04-deliverables/01-高保真图').glob('小暖_*.png')):sources.append((path,'01_高保真设计图/'+path.name))
    assert len(sources)==7
    for name in ['主流程','三通道','异常降级']:
        sources.append((ROOT/f'04-deliverables/02-流程图/小暖_流程图_{name}.pdf',f'02_交互流程图/小暖_流程图_{name}.pdf'))
    sources += [(ROOT/'04-deliverables/04-展板/小暖_展板.pdf','04_展板/小暖_展板_A0.pdf'),(ROOT/'04-deliverables/05-设计说明/小暖_设计说明.pdf','05_设计说明/小暖_设计说明.pdf')]
    for name in ['index.html','screens.js','app.js']:
        sources.append((ROOT/'04-deliverables/06-交互演示'/name,'06_交互演示/'+name))
    for source,_ in sources:
        if not source.is_file():raise FileNotFoundError(source)
    for source,relative in sources:
        target=dest/relative;target.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(source,target)
    (dest/'00_阅读说明.txt').write_text('小暖 · 院内智慧陪诊终端\n本包为非视频交互设计材料：七张PNG、三张流程图、四页A0展板、十二页说明、本地可点击概念演示。\n金额、医嘱、时间与界面反馈均为样例。概念未部署医院，不处理真实支付或通知，不替代医护判断。\n演示：打开06_交互演示/index.html，详细操作见同目录说明。流程图可单独放大阅读。\n视频另行提供；此包不含实名表单和签署文件，不代表已经完成参赛提交。\n',encoding='utf8')
    (dest/'06_交互演示/操作说明.txt').write_text('用桌面Edge或Chrome打开index.html，无需登录或联网。\n七个页签供查看不同页面。入口单击选择通道；入口任意位置长按2秒进入语音，松手后再操作。语音屏长按1.5秒求助，其他屏长按右下求助键1.5秒。\n模拟说话输入：再说一遍、等等、到了、对、好、不对、求助。并不识别麦克风。\n03至少选择一句才可念给医生听。打开演示语音可调用本机中文语音包。\n核对医嘱后查看费用，明确同意才显示家属通知示例；点关闭通知可关闭。拒绝通知仍可归还。\n归还设备会清空本次内存选择；此反馈不是对真实后台安全删除的验证。\n七屏是关键状态，完整11节点逻辑见三张流程图。\n',encoding='utf8')
    (dest/'成员分工.txt').write_text('小暖 · 团队分工\nT1：交互架构、任务流程、统筹、设计说明整合及交付验收；本次统筹补齐界面导出、概念原型和文档排版。\nT2：视觉系统、组件规范及界面草稿。\nT3：交互流程图、视频分镜和解说稿。\nT4：用户研究、原话卡、界面文案与研究说明。\nT5：视频素材与拍摄准备。\n使用生成工具辅助界面、原型及排版制作。视频另行交付。实名作者、指导教师和实际署名顺序另按官方表单由团队确认。\n',encoding='utf8')
    research=(ROOT/'05-research/研究依据摘要-1121.md').read_text(encoding='utf8').split('仓库追溯：')[0]
    (dest/'研究依据摘要.txt').write_text(research,encoding='utf8')
    files=sorted(f for f in dest.rglob('*') if f.is_file())
    manifest={f.relative_to(dest).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    (dest/'文件校验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    zip_path=dest.with_suffix('.zip')
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(dest.rglob('*')):
            if file.is_file():z.write(file,file.relative_to(dest).as_posix())
    assert zip_path.stat().st_size<1024**3
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert not any(set(n.split('/')) & {'.git','.github','.githooks','tools'} for n in z.namelist())
    print(json.dumps({'folder':str(dest),'zip':str(zip_path),'files':len(manifest)+1,'bytes':zip_path.stat().st_size,'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
