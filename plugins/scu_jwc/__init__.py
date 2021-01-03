# -*- coding: utf-8 -*-
from nonebot import on_command, CommandSession
from nonebot.permission import PRIVATE_FRIEND, SUPERUSER

from .utils import usermanager, helpinfo

@on_command('help', aliases=('菜单', '帮助'), permission=PRIVATE_FRIEND)
async def _(session: CommandSession):
    message = "-->{name}<--\n作者：{author}\n版本：{version}\n\n{usage}".format(
        name=helpinfo.NAME, author=helpinfo.AUTHOR, version=helpinfo.VERSION, usage=helpinfo.USAGE
    )
    await session.bot.send_private_msg(user_id=session.event['user_id'], message=message)

@on_command('bind', aliases=('绑定'))
async def command_bind(session: CommandSession):
    qqid = session.event['user_id']
    username = session.get('username', prompt='请输入scu教务处用户名')
    password = session.get('password', prompt='请输入scu教务处密码')
    password = usermanager.password_encryption(password)
    await session.bot.send_private_msg(user_id=qqid, message='密码已经加密\n正在验证账户信息...')

