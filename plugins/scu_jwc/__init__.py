# -*- coding: utf-8 -*-
import aiocqhttp
from nonebot import on_command, on_startup, CommandSession, get_bot, MessageSegment
from nonebot.permission import PRIVATE_FRIEND, SUPERUSER
from .utils import usermanager, helpinfo, jwc_spider

carobot = get_bot()
info_manager = None
spiders = {}

def get_spider(qqid: str):
    global spiders
    spider = spiders.get(qqid, None)
    if spider is None:
        status, queryinfo = info_manager.query_qqid(qqid)
        if queryinfo is None:
            spider = jwc_spider.JWC_Spider(state=0)
        else:
            spider = jwc_spider.JWC_Spider(student_id=queryinfo[0], password=queryinfo[1], state=2)
        spiders[qqid] = spider
    return spider

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
    qqid = str(session.event['user_id'])
    spider = get_spider(qqid)
    if spider is None or spider.state not in [1, 3]: return
    status, b64_img = spider.get_captcha(spider.student_id, spider.password)
    if not status:
        await carobot.send_private_msg(user_id=qqid, message='error: %s' % b64_img)
        return
    await carobot.send_private_msg(user_id=qqid, message='请输入验证码：(输入 "刷新"或"refresh" 更换验证码)')
    await carobot.send_private_msg(user_id=session.event['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))
    spiders[qqid] = spider

@on_command('check', aliases=('验证'))
async def command_check(session: CommandSession, permission=PRIVATE_FRIEND):
    global spiders
    qqid = str(session.event['user_id'])
    spider = get_spider(qqid)
    if spider.state != 2: 
        await carobot.send_private_msg(user_id=qqid, message='请先绑定scu账号\n输入 "绑定" 进行绑定操作')
        return
    if spider.need_reverify():
        spider.state = 3
        status, b64_img = spider.get_captcha(spider.student_id, spider.password)
        if not status:
            await carobot.send_private_msg(user_id=qqid, message='error: %s' % b64_img)
            return
        await carobot.send_private_msg(user_id=qqid, message='请输入验证码：(输入 "刷新"或"refresh" 更换验证码)')
        await carobot.send_private_msg(user_id=session.event['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))
    else:
        status, name = spider.get_name()
        await carobot.send_private_msg(user_id=session.event['user_id'], message="验证成功！\n姓名：%s" % name)
    spiders[qqid] = spider
        

@on_command('unbind', aliases=('解绑'))
async def command_unbind(session: CommandSession, permission=PRIVATE_FRIEND):
    qqid = str(session.event['user_id'])
    status, queryinfo =info_manager.query_qqid(qqid)
    if queryinfo is None:
        await carobot.send_private_msg(user_id=qqid, message='你当前并没有绑定scu账号，操作取消')
        return
    username = session.get('username', prompt='请输入已绑定的scu学号，用来确认解绑操作').strip()
    if username != queryinfo[0]:
        await carobot.send_private_msg(user_id=qqid, message='输入的学号与已绑定的账号不相同，操作取消')
        return
    info_manager.delete_qqid(qqid)
    try: 
        del spiders[qqid]
    except: pass
    await carobot.send_private_msg(user_id=qqid, message='解绑成功！')

@on_command('bind', aliases=('绑定'))
async def command_bind(session: CommandSession, permission=PRIVATE_FRIEND):
    qqid = str(session.event['user_id'])
    spider = get_spider(qqid)

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
    spider.state = 1
    status, b64_img = spider.get_captcha(username, password)
    if not status:
        await carobot.send_private_msg(user_id=qqid, message='error: %s' % b64_img)
        return
    await carobot.send_private_msg(user_id=qqid, message='请输入验证码：(输入 "刷新"或"refresh" 更换验证码)')
    await carobot.send_private_msg(user_id=session.event['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))
    spiders[qqid] = spider

@carobot.on_message('private.friend')
async def handle_captcha(session: aiocqhttp.Event):
    global spiders
    spider = spiders.get(str(session['user_id']), None)
    if spider is None or spider.state not in [1, 3] or len(session['message']) > 1 or session['message'][0]['type'] != 'text': return
    stripped_text = session['message'][0]['data']['text'].strip()
    if len(stripped_text) != 4 or stripped_text in ['menu', 'bind']: return
    status, msg = spider.set_captcha(stripped_text)
    if status and spider.state == 1:
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
        spider.state = 2
    elif status and spider.state == 3:
        status, name = spider.get_name()
        await carobot.send_private_msg(user_id=session['user_id'], message="验证成功！\n姓名：%s" % name)
        spider.state = 2
    elif status == False and spider.state == 3:
        await carobot.send_private_msg(user_id=session['user_id'], message=msg)
        spider.state = 2
    else:
        await carobot.send_private_msg(user_id=session['user_id'], message=msg)
        spider.state = 0
    spiders[str(session['user_id'])] = spider

@on_command('courseTable', aliases=('课表'))
async def command_now_course(session: CommandSession, permission=PRIVATE_FRIEND):
    qqid = str(session.event['user_id'])
    spider = get_spider(qqid)
    if spider.state != 2:
        await carobot.send_private_msg(user_id=qqid, message="未绑定账号，输入 \"bind/绑定\" 进行绑定")
        return
    if spider.need_reverify():
        await carobot.send_private_msg(user_id=qqid, message="账号session已过期，请输入 \"验证\" 进行验证")
        return
    courseList = spider.get_now_course()
    head_msg = f"""
你这学期一共有{courseList['courseNum']}门课
本学期学分：{courseList['totalUnits']}
------------------------------
""".strip()
    body_msg = ''
    for course in courseList['courseList']:
        time_loc_msg = ''
        for tandl in course['time_and_locate']:
            time_loc_msg += f'> 时间：{tandl["time"]}\n> 地点：{tandl["locate"]}\n'
        course_msg = f'''
课程名：{course["courseName"]}
教师：{course["teacher"]}
类型：{course["type"]}
        '''.strip() + "\n"  + time_loc_msg
        body_msg += "\n" + course_msg
    await carobot.send_private_msg(user_id=qqid, message=head_msg + body_msg)
