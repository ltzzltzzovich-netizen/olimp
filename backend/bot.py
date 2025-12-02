import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import sqlite3
from database import get_db_connection

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# TODO: Replace with your actual Token
TOKEN = "8544197831:AAEygWLXCmsvf2YjacMJny9qN_1DBrvFMEI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Dispatcher Bot Started. Use /request <id> to view a request.")

async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a request ID. Usage: /request <id>")
        return

    req_id = context.args[0]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
    req = cursor.fetchone()
    conn.close()

    if not req:
        await update.message.reply_text("Request not found.")
        return

    text = f"Request #{req['id']}\nDescription: {req['description']}\nStatus: {req['status']}"
    
    keyboard = [
        [InlineKeyboardButton("In Progress", callback_data=f"status:In Progress:{req_id}")],
        [InlineKeyboardButton("Processed", callback_data=f"status:Processed:{req_id}")],
        [InlineKeyboardButton("Denied", callback_data=f"status:Denied:{req_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    action = data[0]
    
    if action == "status":
        new_status = data[1]
        req_id = data[2]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, req_id))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(text=f"Request #{req_id} status updated to: {new_status}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('request', request_command))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()
