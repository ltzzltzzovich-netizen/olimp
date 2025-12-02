from flask import Flask, request, jsonify, send_from_directory
import os
import requests as http_requests
from flask_cors import CORS
from models import db, User, Request
from sqlalchemy.exc import IntegrityError

# Import Telegram config from separate file (not tracked by git)
try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    # Fallback for deployment (use environment variables)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quality_control.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def send_telegram_notification(req_id, description, photo_path=None):
    """Send notification to Telegram when a new request is created."""
    try:
        message = f"🚨 *НОВАЯ ЗАЯВКА #{req_id}*\n\n📝 *Описание:* {description}"
        
        # Create inline keyboard with status buttons
        keyboard = {
            'inline_keyboard': [
                [{'text': '🔄 В работе', 'callback_data': f'status:In Progress:{req_id}'}],
                [{'text': '✅ Выполнена', 'callback_data': f'status:Processed:{req_id}'}],
                [{'text': '❌ Отклонена', 'callback_data': f'status:Denied:{req_id}'}],
            ]
        }
        
        if photo_path and os.path.exists(photo_path):
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'
            with open(photo_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                data = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'caption': message,
                    'parse_mode': 'Markdown',
                    'reply_markup': str(keyboard).replace("'", '"')
                }
                http_requests.post(url, data=data, files=files)
        else:
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown',
                'reply_markup': str(keyboard).replace("'", '"')
            }
            http_requests.post(url, data=data)
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")

# Initialize DB
with app.app_context():
    db.create_all()
    # Create default users if not exist
    if not User.query.filter_by(username='worker').first():
        worker = User(username='worker', password_hash='password', full_name='Иван Рабочий', role='worker', shop_id=1)
        db.session.add(worker)
    
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password_hash='admin', full_name='Главный Диспетчер', role='dispatcher')
        db.session.add(admin)

    if not User.query.filter_by(username='master').first():
        master = User(username='master', password_hash='master', full_name='Петр Мастер', role='master', shop_id=1)
        db.session.add(master)
        
    db.session.commit()
    print("Database initialized with SQLAlchemy.")

@app.route('/')
def read_root():
    return jsonify({"message": "Quality Control API is running (Flask + SQLAlchemy)"})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    
    if user and user.password_hash == password:
        return jsonify({
            "token": "fake-jwt-token", 
            "user_id": user.id, 
            "full_name": user.full_name,
            "role": user.role
        })
    return jsonify({"detail": "Invalid credentials"}), 401

@app.route('/requests', methods=['GET'])
def get_requests():
    user_id = request.args.get('user_id')
    role = request.args.get('role') # Optional: filter by role logic if needed

    # If user is a master, show assigned requests + unassigned? 
    # For now, let's keep it simple:
    # Worker -> sees own
    # Dispatcher -> sees all
    # Master -> sees assigned to him
    
    if user_id:
        user = User.query.get(user_id)
        if user:
            if user.role == 'worker':
                requests = Request.query.filter_by(user_id=user_id).order_by(Request.created_at.desc()).all()
            elif user.role == 'master':
                requests = Request.query.filter_by(technician_id=user_id).order_by(Request.created_at.desc()).all()
            else: # dispatcher or others
                requests = Request.query.order_by(Request.created_at.desc()).all()
        else:
             requests = Request.query.order_by(Request.created_at.desc()).all()
    else:
        requests = Request.query.order_by(Request.created_at.desc()).all()
    
    return jsonify([req.to_dict() for req in requests])

@app.route('/requests', methods=['POST'])
def create_request():
    user_id = request.form.get('user_id')
    device_id = request.form.get('device_id')
    description = request.form.get('description')
    photo = request.files.get('photo')

    if not user_id or not description:
        return jsonify({"detail": "Missing required fields"}), 400

    photo_path = None
    if photo:
        filename = photo.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(file_path)
        photo_path = f"uploads/{filename}"

    new_req = Request(
        user_id=user_id,
        device_id=device_id,
        description=description,
        photo_path=photo_path
    )
    db.session.add(new_req)
    db.session.commit()
    
    send_telegram_notification(new_req.id, description, photo_path)
    
    return jsonify({"message": "Request created successfully", "id": new_req.id})

@app.route('/employees', methods=['GET'])
def get_employees():
    # Return all users with role 'master'
    masters = User.query.filter_by(role='master').all()
    
    # Calculate availability (simple logic: available if no IN_PROGRESS tasks)
    result = []
    for m in masters:
        active_tasks = Request.query.filter_by(technician_id=m.id, status='In Progress').count()
        is_available = active_tasks == 0
        result.append({
            "id": m.id,
            "full_name": m.full_name,
            "is_available": is_available,
            "active_tasks": active_tasks
        })
        
    return jsonify(result)

@app.route('/requests/<int:req_id>/assign', methods=['POST'])
def assign_request(req_id):
    data = request.get_json()
    technician_id = data.get('technician_id')
    
    req = Request.query.get(req_id)
    if not req:
        return jsonify({"detail": "Request not found"}), 404
        
    req.technician_id = technician_id
    req.status = 'Assigned'
    db.session.commit()
    
    return jsonify({"message": "Technician assigned", "request": req.to_dict()})

@app.route('/requests/<int:req_id>/status', methods=['POST']) # Using POST for simplicity, or PATCH
def update_request_status(req_id):
    data = request.get_json()
    new_status = data.get('status')
    
    req = Request.query.get(req_id)
    if not req:
        return jsonify({"detail": "Request not found"}), 404
        
    req.status = new_status
    db.session.commit()
    
    return jsonify({"message": "Status updated", "request": req.to_dict()})

# Telegram Bot Integration
def start_telegram_bot():
    """Start Telegram bot in a separate process."""
    from telegram import Update
    from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler
    
    # We need to create a new app context inside the bot process to use DB
    # But sharing the same DB file with SQLite is tricky with multiprocessing.
    # For now, we will use raw sqlite3 in the bot to avoid context issues, 
    # OR we can just use the API to update status?
    # Let's stick to raw sqlite3 for the bot for simplicity in this specific process,
    # as passing the Flask app context to a Process is hard.
    # Ideally, the bot should call the Flask API, but that requires the API to be up.
    
    import sqlite3
    
    def update_status_db(req_id, new_status):
        conn = sqlite3.connect('quality_control.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, req_id))
        conn.commit()
        conn.close()

    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")
        action = data[0]
        
        if action == "status":
            new_status = data[1]
            req_id = data[2]
            
            update_status_db(req_id, new_status)
            
            status_translations = {
                'In Progress': 'В работе',
                'Processed': 'Выполнена',
                'Denied': 'Отклонена'
            }
            translated_status = status_translations.get(new_status, new_status)
            
            await query.edit_message_text(
                text=f"✅ Заявка #{req_id}\nСтатус обновлен: *{translated_status}*",
                parse_mode='Markdown'
            )
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 Telegram Bot started and listening for updates...")
    application.run_polling()

if __name__ == '__main__':
    from multiprocessing import Process
    
    # Start Telegram bot
    bot_process = Process(target=start_telegram_bot)
    bot_process.start()
    
    # Start Flask server
    try:
        app.run(host='0.0.0.0', port=8000, debug=False)
    finally:
        bot_process.terminate()
        bot_process.join()
