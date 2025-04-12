import os
import subprocess
import logging
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengirim pesan ketika command /start digunakan."""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("LOE SIAPA?")
        return

    await update.message.reply_text(
        '2026 ganti gaya'
    )

async def check_permission(update: Update):
    """Memeriksa apakah pengguna memiliki izin"""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("Maaf, Anda tidak memiliki izin untuk menggunakan bot ini.")
        return False
    return True

async def run_command(update: Update, command, working_dir=None, success_msg=None):
    """Menjalankan perintah dan mengembalikan hasilnya"""
    try:
        if working_dir:
            os.chdir(working_dir)
            
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=isinstance(command, str)
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            result = stdout.decode('utf-8')
            message = success_msg if success_msg else f"Perintah berhasil dijalankan:\n\n```\n{result}\n```"
            await update.message.reply_text(message)
            return True
        else:
            error = stderr.decode('utf-8')
            await update.message.reply_text(f"Error saat menjalankan perintah:\n\n```\n{error}\n```")
            return False
            
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")
        return False

async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjalankan git pull pada repository."""
    if not await check_permission(update):
        return
    
    await update.message.reply_text('Menjalankan git pull...')
    await run_command(
        update, 
        ['git', 'pull'], 
        working_dir=REPO_PATH,
        success_msg="Git pull berhasil dilakukan!"
    )

async def pushdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjalankan npx prisma db push."""
    if not await check_permission(update):
        return
    
    await update.message.reply_text('Menjalankan npx prisma db push...')
    await run_command(
        update, 
        ['npx', 'prisma', 'db', 'push'], 
        working_dir=REPO_PATH,
        success_msg="Database berhasil diupdate dengan prisma db push!"
    )

async def restart_backend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Merestart service backend."""
    if not await check_permission(update):
        return
    
    await update.message.reply_text('Merestart service backend...')
    await run_command(
        update, 
        'systemctl restart backend', 
        success_msg="Service backend berhasil direstart!"
    )

def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN tidak ditemukan di file .env")
        return
        
    if not ALLOWED_USER_IDS:
        logging.error("ALLOWED_USER_IDS tidak ditemukan di file .env")
        return
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pull", pull))
    application.add_handler(CommandHandler("pushdb", pushdb))
    application.add_handler(CommandHandler("restart", restart_backend))

    logging.info("Bot mulai berjalan...")
    application.run_polling()

if __name__ == '__main__':
    main()
