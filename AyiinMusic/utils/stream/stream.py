#
# Copyright (C) 2021-2022 by AyiinXd@Github, < https://github.com/AyiinXd >.
#
# This file is part of < https://github.com/AyiinXd/AyiinMusicBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/AyiinXd/AyiinMusicBot/blob/master/LICENSE >
#
# All rights reserved.

import os
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from AyiinMusic import Carbon, YouTube, app
from AyiinMusic.core.call import Ayiin
from AyiinMusic.misc import db
from AyiinMusic.utils.database import (add_active_chat,
                                       add_active_video_chat,
                                       is_active_chat,
                                       is_video_allowed, music_on)
from AyiinMusic.utils.exceptions import AssistantErr
from AyiinMusic.utils.inline.play import (stream_markup,
                                          telegram_markup)
from AyiinMusic.utils.inline.playlist import close_markup
from AyiinMusic.utils.pastebin import Ayiinbin
from AyiinMusic.utils.stream.queue import put_queue, put_queue_index
from AyiinMusic.utils.thumbnails import gen_thumb


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
):
    if video:
        if not await is_video_allowed(chat_id):
            raise AssistantErr(_["play_6"])
    if streamtype == "playlist":
        msg = f"{_['playlist_16']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(
                    search, False if spotify else True
                )
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}- {title[:70]}\n"
                msg += f"{_['playlist_17']} {position}\n\n"
            else:
                db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except:
                    raise AssistantErr(_["play_16"])
                await Ayiin.join_call(
                    chat_id, original_chat_id, file_path, video=status
                )
                await add_active_chat(chat_id)
                await music_on(chat_id)
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                if video:
                    await add_active_video_chat(chat_id)
                img = await gen_thumb(vidid)
                button = stream_markup(_, vidid)
                await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                    f"[{title[:25]}](https://t.me/{app.username}?start=info_{vidid})", duration_min, user_name,
                ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
        if count == 0:
            return
        else:
            link = await Ayiinbin(msg)
            lines = msg.count("\n")
            if lines >= 17:
                car = os.linesep.join(msg.split(os.linesep)[:17])
            else:
                car = msg
            carbon = await Carbon.generate(
                car, randint(100, 10000000)
            )
            upl = close_markup(_)
            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["playlist_18"].format(link, position),
                reply_markup=upl,
            )
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        status = True if video else None
        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except:
            raise AssistantErr(_["play_16"])
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )
        else:
            db[chat_id] = []
            await Ayiin.join_call(
                chat_id, original_chat_id, file_path, video=status
            )
            await add_active_chat(chat_id)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            if video:
                await add_active_video_chat(chat_id)
            await music_on(chat_id)
            img = await gen_thumb(vidid)
            button = stream_markup(_, vidid)
            await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"[{title[:25]}](https://t.me/{app.username}?start=info_{vidid})", duration_min, user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )
        else:
            db[chat_id] = []
            await Ayiin.join_call(
                chat_id, original_chat_id, file_path, video=None
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            if video:
                await add_active_video_chat(chat_id)
            await music_on(chat_id)
            await add_active_chat(chat_id)
            button = telegram_markup(_)
            await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_3"].format(
                    title[:25], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:25], duration_min, user_name
                ),
            )
        else:
            db[chat_id] = []
            await Ayiin.join_call(
                chat_id, original_chat_id, file_path, video=status
            )
            await add_active_chat(chat_id)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            if video:
                await add_active_video_chat(chat_id)
            await music_on(chat_id)
            button = telegram_markup(_)
            await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL
                if video
                else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_4"].format(
                    title[:25], link, duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                ),
            )
        else:
            db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await Ayiin.join_call(
                chat_id, original_chat_id, file_path, video=status
            )
            await add_active_chat(chat_id)
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            if video:
                await add_active_video_chat(chat_id)
            await music_on(chat_id)
            img = await gen_thumb(vidid)
            button = telegram_markup(_)
            await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"[{title[:25]}](https://t.me/{app.username}?start=info_{vidid})", duration_min, user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
    elif streamtype == "index":
        link = result
        title = "Index or M3u8 Link"
        duration_min = "URL stream"
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video",
            )
            position = len(db.get(chat_id)) - 1
            await mystic.edit_text(
                _["queue_4"].format(
                    position, title[:30], duration_min, user_name
                )
            )
        else:
            db[chat_id] = []
            await Ayiin.join_call(
                chat_id, original_chat_id, link, video=True
            )
            await add_active_chat(chat_id)
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video",
            )
            await add_active_video_chat(chat_id)
            await music_on(chat_id)
            button = telegram_markup(_)
            await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            await mystic.delete()
