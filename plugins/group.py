import nonebot
from nonebot import on_notice, NoticeSession

@on_notice('group_increase')
async def _(session: NoticeSession):
    await session.send('欢迎新朋友!', at_sender=True)

