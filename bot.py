#!/usr/bin/env python3
"""
CompressMasterBot v2.8
-----------------------
Final stable release.

Features:
 - Fast & safe Telegram file download
 - Stable FFmpeg compression
 - Multi-quality support
 - Cancelable tasks
 - Full async (python-telegram-bot v20+)

Folder Structure:
  bot.py
  app/
    core/config.py
    utils/downloader.py
    utils/compressor.py
    utils/uploader.py
"""

import asyncio
import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from app.core.config import settings
from app.utils.downloader import download_file
from app.utils.compressor import compress_video
from app.utils.uploader import send_video

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Active tasks (for cancel support)
ACTIVE_TASKS = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to **CompressMasterBot v2.8**\n\n"
        "Send me any *video* and I will compress it.\n"
        "Choose from 480p, 720p or 1080p."
    )


async def handle_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    keyboard = [
        [
            InlineKeyboardButton("480p", callback_data="480"),
            InlineKeyboardButton("720p", callback_data="720"),
            InlineKeyboardButton("1080p", callback_data="1080"),
        ]
    ]

    await msg.reply_text(
        "Select compression quality:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data["file_id"] = msg.video.file_id
    context.user_data["original_name"] = msg.video.file_name


async def quality_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data
    file_id = context.user_data.get("file_id")
    original_name = context.user_data.get("original_name")

    if not file_id:
        return await query.edit_message_text("❌ Error: No file found. Send video again.")

    message = await query.edit_message_text("📥 Downloading...")

    # Start background task
    task = asyncio.create_task(
        process_video(file_id, original_name, quality, message, context)
    )
    ACTIVE_TASKS[query.from_user.id] = task


async def process_video(file_id, original_name, quality, message, context):
    user_id = message.chat_id

    try:
        # Download
        await message.edit_text("📥 Downloading...")
        input_path = await download_file(context, file_id)

        # Compress
        await message.edit_text(f"🎬 Compressing ({quality}p)...")
        output_path = await compress_video(input_path, quality)

        # Upload
        await message.edit_text("📤 Uploading...")
        await send_video(context, user_id, output_path, original_name)

        await message.edit_text("✅ Done!")

    except asyncio.CancelledError:
        await message.edit_text("❌ Compression cancelled.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.edit_text("⚠️ Compression failed.")
    finally:
        if user_id in ACTIVE_TASKS:
            del ACTIVE_TASKS[user_id]

        # Cleanup files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in ACTIVE_TASKS:
        ACTIVE_TASKS[user_id].cancel()
        return await update.message.reply_text("🛑 Task cancelled successfully.")
    else:
        return await update.message.reply_text("⚠️ No active task to cancel.")


def main():
    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video_message))
    app.add_handler(CallbackQueryHandler(quality_selected))

    logger.info("Bot started successfully.")
    app.run_polling()


if __name__ == "__main__":
    main()
