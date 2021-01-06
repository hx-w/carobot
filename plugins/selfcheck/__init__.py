from random import choice

from nonebot import on_command, CommandSession, permission

from .data_source import Check
from nonebot import get_bot
from nonebot.permission import SUPERUSER

Bot = get_bot()
MAX_PERFORMANCE_PERCENT = Bot.config.MAX_PERFORMANCE_PERCENT
PROCESS_NAME_LIST = Bot.config.PROCESS_NAME_LIST
SUPERUSERS = Bot.config.SUPERUSERS


__plugin_name__ = '自我检查'
__plugin_usage__ = r"""
进行一次简单的自我检查
如果检查出问题会通知管理员的
*注意并不能检测所有问题，如果发现了问题，请及时反馈*
check [无参数]
自检 [无参数]
""".strip()


check = Check(Bot.config.PROCESS_NAME_LIST)

@on_command('selfcheck', aliases=('自检'), permission=SUPERUSER)
async def selfcheck(session: CommandSession):
    check_report = await check.get_check_easy(MAX_PERFORMANCE_PERCENT)
    more_info = '[CQ:at,qq={}]'.format(choice(list(SUPERUSERS))) if (SUPERUSERS and session.event['message_type'] == 'group') else "\n请联系管理员修复Bot"
    if check_report:
        if SUPERUSERS:
            for admin in SUPERUSERS:
                await Bot.send_private_msg(user_id=admin, message='我好像生病了')
    check_report_admin = await check.get_check_info()

    await session.send(check_report_admin)
    await session.send("自检结束，服务器状态正常")
