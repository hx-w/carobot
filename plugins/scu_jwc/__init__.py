# -*- coding: utf-8 -*-
import aiocqhttp
from nonebot import on_command, on_startup, CommandSession, get_bot, MessageSegment
from nonebot.permission import PRIVATE_FRIEND, SUPERUSER
from .utils import usermanager, helpinfo, jwc_spider

carobot = get_bot()
info_manager = None
spiders = {}

@on_startup
def startup():
    global info_manager
    info_manager = usermanager.InfoManager(
        db_host = carobot.config.DB_HOST,
        db_user = carobot.config.DB_USER,
        db_name = carobot.config.DB_NAME,
        db_password = carobot.config.DB_PASSWORD,
        db_table_name = carobot.config.DB_TABLE_NAME
    )

@on_command('menu', aliases=('菜单', '帮助'), permission=PRIVATE_FRIEND)
async def _(session: CommandSession):
    message = "===== {name} =====\n作者：{author}\n版本：{version}\n\n{usage}".format(
        name=helpinfo.NAME, author=helpinfo.AUTHOR, version=helpinfo.VERSION, usage=helpinfo.USAGE
    )
    await carobot.send_private_msg(user_id=session.event['user_id'], message=message)

@on_command('refresh_captcha', aliases=('refresh', '刷新'))
async def command_refresh_captcha(session: CommandSession, permission=PRIVATE_FRIEND):
    qqid = session.event['user_id']
    spider = spiders.get(qqid, None)
    if spider is None or spider.state != 1: return
    status, b64_img = spider.get_captcha(spider.student_id, spider.password)
    if not status:
        await carobot.send_private_msg(user_id=qqid, message='error: %s' % b64_img)
        return
    await carobot.send_private_msg(user_id=qqid, message='请输入验证码：(输入 "刷新"或"refresh" 更换验证码)')
    await carobot.send_private_msg(user_id=session.event['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))
    spiders[qqid] = spider

@on_command('bind', aliases=('绑定'))
async def command_bind(session: CommandSession, permission=PRIVATE_FRIEND):
    qqid = session.event['user_id']
    spider = spiders.get(qqid, None)
    if spider is None:
        status, queryinfo = info_manager.query_qqid(qqid)
        if not status:
            await carobot.send_private_msg(user_id=qqid, message='error：%s' % queryinfo)
            return
        if queryinfo is None:
            spider = jwc_spider.JWC_Spider()
        else:
            spider = jwc_spider.JWC_Spider(student_id=queryinfo[0], password=queryinfo[1], state=2)

    if spider.state == 1: return
    if spider.state == 2:
        status, queryinfo = info_manager.query_qqid(qqid)
        if not status:
            await carobot.send_private_msg(user_id=qqid, message='error：%s' % queryinfo)
            return
        await carobot.send_private_msg(user_id=qqid, message=f'已绑定学生账号：【{queryinfo[0]}】\n输入 "check/验证" 进行验证\n输入 "unbind/解绑" 解绑账号')
        return

    username = session.get('username', prompt='请输入scu学号')
    password = session.get('password', prompt='请输入scu教务处密码')
    password = usermanager.password_encryption(password)
    await carobot.send_private_msg(user_id=qqid, message='密码已加密, 正在验证账户信息')
    
    #### 拿验证码
    status, b64_img = spider.get_captcha(username, password)
    if not status:
        await carobot.send_private_msg(user_id=qqid, message='error: %s' % b64_img)
        return
    await carobot.send_private_msg(user_id=qqid, message='请输入验证码：(输入 "刷新"或"refresh" 更换验证码)')
    await carobot.send_private_msg(user_id=session.event['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))
    spiders[qqid] = spider

@carobot.on_message('private.friend')
async def handle_captcha(session: aiocqhttp.Event):
    spider = spiders.get(session['user_id'], None)
    if spider is None or spider.state != 1 or len(session['message']) > 1 or session['message'][0]['type'] != 'text': return
    if session['message'][0]['data']['text'].strip() in ['刷新', 'refresh', '菜单', 'menu', '绑定', 'bind']: return
    stripped_text = session['message'][0]['data']['text'].strip()
    status, msg = spider.set_captcha(stripped_text)
    if status:
        info_manager.insert(student_id=spider.student_id, password=spider.password, qq_id=session['user_id'])
        status, name = spider.get_name()
        if not status:
            await carobot.send_private_msg(user_id=session['user_id'], message="error：%s" % name)
            return
        status, b64_img = spider.get_headPic()
        if not status:
            await carobot.send_private_msg(user_id=session['user_id'], message="error：%s" % b64_img)
            return
        await carobot.send_private_msg(user_id=session['user_id'], message="验证成功！\n姓名：%s" % name)
        await carobot.send_private_msg(user_id=session['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))
        return

    spider.state = 2 if status else 0
    await carobot.send_private_msg(user_id=session['user_id'], message="error：%s" % msg)
    spiders[session['user_id']] = spider

