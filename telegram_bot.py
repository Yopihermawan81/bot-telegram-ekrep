import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Inisialisasi Firebase
basedir = os.path.dirname(__file__)
cred_path = os.path.join(basedir, "serviceAccountKey.json")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔁 Fungsi normalisasi nomor HP
def normalize_phone(input_str: str) -> str:
    input_str = input_str.strip().replace(" ", "").replace("-", "")
    if input_str.startswith("0"):
        return "+62" + input_str[1:]
    elif input_str.startswith("62"):
        return "+" + input_str
    elif input_str.startswith("+62"):
        return input_str
    return "+62" + input_str

# Handler /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Halo {user.first_name or 'teman'}! 👋\n\n"
        "Silakan kirim nomor HP Telegram kamu (misalnya: 08xxxxxxxxxx) untuk menghubungkan akun eKreP-mu."
    )

# Handler pesan teks (nomor HP)
async def handle_hp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    raw_hp = update.message.text.strip()
    no_hp = normalize_phone(raw_hp)

    if not no_hp.startswith("+628") or len(no_hp) < 11:
        await update.message.reply_text("⚠️ Nomor HP tidak valid. Gunakan format 08xxxxxxxxxx.")
        return

    nama = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # Simpan ke Firestore
    db.collection("telegram_chat_ids").document(no_hp).set({
        "chat_id": chat_id,
        "nama": nama,
        "username": user.username or "",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    await update.message.reply_text(
        f"✅ Terima kasih, {nama}!\n"
        f"Akun Telegram ini telah dikaitkan dengan nomor HP {no_hp}.\n\n"
        f"👉 Sekarang kamu bisa kembali ke aplikasi eKreP untuk lanjut daftar."
    )

# Jalankan bot
if __name__ == '__main__':
    app = ApplicationBuilder().token("7902879933:AAGXoPwWcgwrEVxAdFVvUe_ivbCUYGe1YqI").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hp))

    print("🤖 Bot aktif... tekan Ctrl+C untuk keluar.")
    app.run_polling()
