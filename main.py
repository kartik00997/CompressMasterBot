#!/usr/bin/env python3
"""
CompressMasterBot v2.8
Fully optimized Telegram media compressor bot.
"""

import os
import asyncio
import logging
from config import settings
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
import subprocess
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------------
# Start Command
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to CompressMasterBot v2.8\n"
        "Send any video and I will compress it!"
    )

# ----------------------------
# Compression Function
# ----------------------------
async def compress_video(input_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "28",
        "-preset", "veryfast",
        "-acodec", "aac",
        output_path
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    await process.communicate()


# ----------------------------
# Handle Videos
# ----------------------------
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message.video:
        return

    file_id = message.video.file_id
    tg_file = await context.bot.get_file(file_id)

    # Random filenames
    input_file = f"{settings.TEMP_DIR}/{uuid.uuid4()}.mp4"
    output_file = f"{settings.TEMP_DIR}/{uuid.uuid4()}_compressed.mp4"

    # Download video
    await tg_file.download_to_drive(input_file)
    await message.reply_text("📥 Downloaded! Compressing…")

    # Compress video
    await compress_video(input_file, output_file)
    await message.reply_text("📤 Uploading compressed video…")

    # Send compressed video
    await message.reply_video(output_file)

    # Cleanup
    os.remove(input_file)
    os.remove(output_file)


# ----------------------------
# MAIN FUNCTION
# ----------------------------
async def main():
    bot_token = settings.BOT_TOKEN

    if not bot_token:
        print("BOT_TOKEN missing in environment!")
        return

    app = (
        ApplicationBuilder()
        .token(bot_token)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
