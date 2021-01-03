# -*- coding: utf-8 -*-
from nonebot import on_command, on_startup, CommandSession, get_bot, MessageSegment
from nonebot.permission import PRIVATE_FRIEND, SUPERUSER
from .utils import usermanager, helpinfo, jwc_spider

carobot = None
info_manager = None
spiders = {}

@on_startup
def startup():
    global carobot, info_manager
    carobot = get_bot()
    info_manager = usermanager.InfoManager(
        db_host = carobot.config.DB_HOST,
        db_user = carobot.config.DB_USER,
        db_name = carobot.config.DB_NAME,
        db_password = carobot.config.DB_PASSWORD,
        db_table_name = carobot.config.DB_TABLE_NAME
    )

@on_command('menu', aliases=('菜单', '帮助'), permission=PRIVATE_FRIEND)
async def _(session: CommandSession):
    message = "==={name}===\n作者：{author}\n版本：{version}\n\n{usage}".format(
        name=helpinfo.NAME, author=helpinfo.AUTHOR, version=helpinfo.VERSION, usage=helpinfo.USAGE
    )
    await carobot.send_private_msg(user_id=session.event['user_id'], message=message)

@on_command('bind', aliases=('绑定'))
async def command_bind(session: CommandSession, permission=PRIVATE_FRIEND):
    qqid = session.event['user_id']
    username = session.get('username', prompt='请输入scu学号')
    password = session.get('password', prompt='请输入scu教务处密码')
    password = usermanager.password_encryption(password)
    await carobot.send_private_msg(user_id=qqid, message='密码已加密, 正在验证账户信息')
    
    global spiders
    spider = spiders.get(username, None)
    if spider is None:
        spider = jwc_spider.JWC_Spider()
    #### 拿验证码
    status, b64_img = spider.get_captcha(username, password)
    if not status:
        await carobot.send_private_msg(user_id=qqid, message='error: %s' % b64_img)
        return
    await carobot.send_private_msg(user_id=qqid, message='请输入验证码：')
    await carobot.send_private_msg(user_id=session.event['user_id'], message=MessageSegment({"type": "image", "data": {"file": b64_img}}))

