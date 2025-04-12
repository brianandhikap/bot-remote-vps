import os
import subprocess
import logging
import time
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_IDS = [int(id.strip()) for id in os.getenv("ALLOWED_USER_IDS", "").split(",") if id.strip()]

REPO_PATH = os.getenv("REPO_PATH")

latest_update = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan ketika command /start digunakan."""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("LOE SIAPA?")
        return

    await update.message.reply_text(
        '2026 ganti GAYA'
    )

async def check_permission(update: Update):
    """Memeriksa apakah pengguna memiliki izin"""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("Maaf, Anda tidak memiliki izin untuk menggunakan bot ini.")
        return False
    return True

async def git_pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjalankan git pull dengan deteksi repository private."""
    if not await check_permission(update):
        return
    
    await update.message.reply_text('Menjalankan git pull...')
    
    try:
        os.chdir(REPO_PATH)
        
        process = subprocess.run(
            "GIT_TERMINAL_PROMPT=0 git pull",
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        output = process.stdout + process.stderr
        
        if "Authentication failed" in output or "could not read Username" in output:
            await update.message.reply_text("repositori private")
        elif process.returncode == 0:
            await update.message.reply_text(f"Git pull berhasil dilakukan!\n\n```\n{process.stdout}\n```")
        else:
            try:
                test_process = subprocess.run(
                    "git pull",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=1
                )
            except subprocess.TimeoutExpired:
                await update.message.reply_text("repositori private")
                return
                
            await update.message.reply_text(f"Error saat menjalankan git pull:\n\n```\n{process.stderr}\n```")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("repositori private")
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

async def pushdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjalankan npx prisma db push."""
    if not await check_permission(update):
        return
    
    await update.message.reply_text('Menjalankan npx prisma db push...')
    
    try:
        os.chdir(REPO_PATH)
        
        process = subprocess.run(
            ["npx", "prisma", "db", "push"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if process.returncode == 0:
            await update.message.reply_text(f"Database berhasil diupdate dengan prisma db push!\n\n```\n{process.stdout}\n```")
        else:
            await update.message.reply_text(f"Error saat menjalankan npx prisma db push:\n\n```\n{process.stderr}\n```")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Operasi timeout. Periksa server secara manual.")
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

async def restart_backend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Merestart service backend."""
    if not await check_permission(update):
        return
    
    await update.message.reply_text('Merestart service backend...')
    
    try:
        process = subprocess.run(
            ["systemctl", "restart", "backend"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if process.returncode == 0:
            await update.message.reply_text("Service backend berhasil direstart!")
        else:
            await update.message.reply_text(f"Error saat merestart backend:\n\n```\n{process.stderr}\n```")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Operasi timeout. Periksa server secara manual.")
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN tidak ditemukan di file .env")
        return
        
    if not ALLOWED_USER_IDS:
        logging.error("ALLOWED_USER_IDS tidak ditemukan di file .env")
        return
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pull", git_pull))
    application.add_handler(CommandHandler("pushdb", pushdb))
    application.add_handler(CommandHandler("restart", restart_backend))

    logging.info("Bot mulai berjalan...")
    application.run_polling()

if __name__ == '__main__':
    main()
