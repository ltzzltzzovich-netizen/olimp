from flask import Flask, request, jsonify, send_from_directory, send_file, render_template
import os
import requests as http_requests
import requests as http_requests
import openpyxl
from io import BytesIO
from flask_cors import CORS
from models import db, User, Request, STATUS_TRANSLATIONS
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

# PostgreSQL Config
# Format: postgresql://user:password@localhost:5432/dbname
# Try to get from env, else use default local
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:postgres@localhost:5432/quality_control'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def send_telegram_notification(req_id, description, photo_path=None):
    """Send notification to Telegram when a new request is created."""
    try:
        message = f"🚨 *НОВАЯ ЗАЯВКА #{req_id}*\n\n📝 *Описание:* {description}"
        
        # Create inline keyboard with status buttons
        keyboard = {
            'inline_keyboard': [
                [{'text': '✅ В работу', 'callback_data': f'assign_menu:{req_id}'}], 
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

@app.route('/reports/export', methods=['GET'])
def export_report():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requests Report"
    
    # Headers
    headers = ['ID', 'Date', 'Author', 'Description', 'Master', 'Status', 'Equipment ID']
    ws.append(headers)
    
    requests = Request.query.all()
    for req in requests:
        ws.append([
            req.id,
            req.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            req.author.full_name if req.author else 'Unknown',
            req.description,
            req.technician.full_name if req.technician else '-',
            STATUS_TRANSLATIONS.get(req.status, req.status),
            req.device_id if req.device_id else '-'
        ])
        
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='requests_report.xlsx'
    )

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

# =====================
# ADMIN CRUD: Users
# =====================
@app.route('/admin/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/admin/users', methods=['POST'])
def create_user():
    data = request.json
    try:
        user = User(
            username=data['username'],
            password_hash=data['password'],
            full_name=data['full_name'],
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    try:
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'role' in data:
            user.role = data['role']
        if 'password' in data and data['password']:
            user.password_hash = data['password']
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# =====================
# ADMIN CRUD: Equipment
# =====================
from models import Equipment

@app.route('/admin/equipment', methods=['GET'])
def get_equipment():
    equipment = Equipment.query.all()
    return jsonify([e.to_dict() for e in equipment])

@app.route('/admin/equipment', methods=['POST'])
def create_equipment():
    data = request.json
    try:
        eq = Equipment(
            name=data['name'],
            code=data['code'],
            shop_id=data.get('shop_id')
        )
        db.session.add(eq)
        db.session.commit()
        return jsonify(eq.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Equipment code already exists"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/equipment/<int:eq_id>', methods=['PUT'])
def update_equipment(eq_id):
    eq = Equipment.query.get_or_404(eq_id)
    data = request.json
    try:
        if 'name' in data:
            eq.name = data['name']
        if 'code' in data:
            eq.code = data['code']
        if 'shop_id' in data:
            eq.shop_id = data['shop_id']
        db.session.commit()
        return jsonify(eq.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/equipment/<int:eq_id>', methods=['DELETE'])
def delete_equipment(eq_id):
    eq = Equipment.query.get_or_404(eq_id)
    try:
        db.session.delete(eq)
        db.session.commit()
        return jsonify({"message": "Equipment deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# =====================
# ADMIN: Requests List
# =====================
@app.route('/admin/requests', methods=['GET'])
def get_all_requests():
    requests_list = Request.query.all()
    return jsonify([r.to_dict() for r in requests_list])

@app.route('/admin/requests/<int:req_id>', methods=['PUT'])
def update_request(req_id):
    req = Request.query.get_or_404(req_id)
    data = request.json
    try:
        if 'status' in data:
            req.status = data['status']
        if 'description' in data:
            req.description = data['description']
        if 'technician_id' in data:
            req.technician_id = data['technician_id'] if data['technician_id'] else None
        db.session.commit()
        return jsonify(req.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/requests/<int:req_id>', methods=['DELETE'])
def delete_request(req_id):
    req = Request.query.get_or_404(req_id)
    try:
        db.session.delete(req)
        db.session.commit()
        return jsonify({"message": "Request deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/reset_requests', methods=['POST'])
def reset_requests():
    try:
        num_deleted = db.session.query(Request).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted {num_deleted} requests"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/admin/seed', methods=['POST'])
def seed_db():
    try:
        # Create tables if not exist (including new Equipment table)
        db.create_all()
        
        # Add sample users if they don't exist
        users_data = [
            {"username": "worker2", "full_name": "Алексей Петров", "role": "worker", "password": "password"},
            {"username": "worker3", "full_name": "Дмитрий Сидоров", "role": "worker", "password": "password"},
            {"username": "master2", "full_name": "Сергей Мастеров", "role": "master", "password": "master"},
            {"username": "master3", "full_name": "Андрей Главный", "role": "master", "password": "master"},
        ]
        
        added_users = 0
        for u_data in users_data:
            if not User.query.filter_by(username=u_data['username']).first():
                new_user = User(
                    username=u_data['username'],
                    full_name=u_data['full_name'],
                    role=u_data['role'],
                    password_hash=u_data['password'] # In real app, hash this!
                )
                db.session.add(new_user)
                added_users += 1
        
        # Add sample equipment
        from models import Equipment
        equipment_data = [
            {"name": "Токарный станок CNC-1", "code": "CNC-001", "shop_id": 1},
            {"name": "Фрезерный станок MIL-2", "code": "MIL-002", "shop_id": 1},
            {"name": "Пресс гидравлический P-50", "code": "PRS-050", "shop_id": 2},
            {"name": "Сварочный робот KUKA", "code": "RBT-001", "shop_id": 3},
        ]
        
        added_equipment = 0
        for eq_data in equipment_data:
            if not Equipment.query.filter_by(code=eq_data['code']).first():
                new_eq = Equipment(
                    name=eq_data['name'],
                    code=eq_data['code'],
                    shop_id=eq_data['shop_id']
                )
                db.session.add(new_eq)
                added_equipment += 1
                
        db.session.commit()
        
        return jsonify({
            "message": "Database seeded successfully",
            "users_added": added_users,
            "equipment_added": added_equipment
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ... (DB init code remains same) ...

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

@app.route('/requests/<int:req_id>/status', methods=['POST'])
def update_request_status(req_id):
    data = request.get_json()
    new_status = data.get('status')
    
    req = Request.query.get(req_id)
    if not req:
        return jsonify({"detail": "Request not found"}), 404
    
    old_status = req.status    
    req.status = new_status
    db.session.commit()
    
    # Send notification to dispatcher when work is completed
    if new_status == 'Completed' and old_status != 'Completed':
        try:
            master_name = req.technician.full_name if req.technician else "Неизвестный мастер"
            message = (
                f"✅ *ЗАЯВКА #{req_id} ВЫПОЛНЕНА*\n\n"
                f"👷 *Мастер:* {master_name}\n"
                f"📝 *Описание:* {req.description}\n\n"
                f"🎉 Мастер свободен и готов к новым заявкам"
            )
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
            data_payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }
            http_requests.post(url, data=data_payload)
        except Exception as e:
            print(f"Failed to send completion notification: {e}")
    
    return jsonify({"message": "Status updated", "request": req.to_dict()})


# Telegram Bot Webhook Integration
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, CommandHandler

# ... (Previous code)

async def report_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Generate report
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requests Report"
    headers = ['ID', 'Date', 'Author', 'Description', 'Master', 'Status', 'Equipment ID']
    ws.append(headers)
    
    # Fetch data using psycopg2 directly
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.created_at, u.full_name, r.description, t.full_name, r.status, r.device_id 
        FROM requests r
        LEFT JOIN users u ON r.user_id = u.id
        LEFT JOIN users t ON r.technician_id = t.id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        # Translate status
        status = STATUS_TRANSLATIONS.get(row[5], row[5])
        ws.append([
            row[0],
            row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else '',
            row[2] or 'Unknown',
            row[3],
            row[4] or '-',
            status,
            row[6] or '-'
        ])
        
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    await context.bot.send_document(
        chat_id=chat_id,
        document=output,
        filename='requests_report.xlsx',
        caption='📊 Отчет по заявкам'
    )

# ... (Existing button_handler)

def start_background_bot_loop():
    """Runs the Telegram bot in a dedicated background thread with a permanent event loop."""
    global background_loop, telegram_app
    
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    background_loop = loop
    
    # Initialize the application inside this loop
    telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(CommandHandler("report", report_command_handler))
import asyncio
import threading
import time
import psycopg2

# Global variables
background_loop = None
telegram_app = None

# --- Database Helpers for Bot ---
def get_db_connection():
    DB_DSN = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/quality_control')
    return psycopg2.connect(DB_DSN)

def get_masters():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name FROM users WHERE role = 'master'")
    masters = cursor.fetchall()
    conn.close()
    return masters

def update_status_db(req_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET status = %s WHERE id = %s", (new_status, req_id))
    conn.commit()
    conn.close()

def assign_master_db(req_id, master_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET technician_id = %s, status = 'Assigned' WHERE id = %s", (master_id, req_id))
    conn.commit()
    conn.close()
    
def get_master_name(master_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE id = %s", (master_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Unknown"

# --- Bot Handlers ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action = data[0]
    
    async def edit_message(text, reply_markup=None):
        if query.message.photo:
            await query.edit_message_caption(
                caption=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    try:
        if action == "status":
            new_status = data[1]
            req_id = data[2]
            
            update_status_db(req_id, new_status)
            translated_status = STATUS_TRANSLATIONS.get(new_status, new_status)
            
            original_text = query.message.caption if query.message.photo else query.message.text
            # Keep only the description part
            base_text = original_text.split('\n\n✅')[0].split('\n\n⚠️')[0].split('\n\n👷')[0].split('\n\n❌')[0]
            
            await edit_message(f"{base_text}\n\n❌ Статус обновлен: *{translated_status}*")
            
        elif action == "assign_menu":
            req_id = data[1]
            masters = get_masters()
            
            original_text = query.message.caption if query.message.photo else query.message.text
            base_text = original_text.split('\n\n✅')[0].split('\n\n⚠️')[0].split('\n\n👷')[0].split('\n\n❌')[0]

            if not masters:
                await edit_message(f"{base_text}\n\n⚠️ Нет доступных мастеров для назначения.")
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            
            keyboard = []
            for m_id, m_name in masters:
                cursor.execute(
                    "SELECT COUNT(*) FROM requests WHERE technician_id = %s AND status = 'In Progress'",
                    (m_id,)
                )
                active_count = cursor.fetchone()[0]
                
                if active_count == 0:
                    keyboard.append([InlineKeyboardButton(f"✅ {m_name} (Свободен)", callback_data=f"assign:{m_id}:{req_id}")])
                else:
                    keyboard.append([InlineKeyboardButton(f"⏳ {m_name} (Занят - {active_count})", callback_data=f"busy:{m_id}")])
            
            conn.close()
            
            if not any('assign:' in btn[0].callback_data for btn in keyboard):
                await edit_message(f"{base_text}\n\n⚠️ Все мастера заняты. Попробуйте позже.")
                return
            
            keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data=f"cancel_assign:{req_id}")])
            
            await edit_message(f"{base_text}\n\n👷 **Выберите свободного мастера:**",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif action == "assign":
            master_id = data[1]
            req_id = data[2]
            
            assign_master_db(req_id, master_id)
            master_name = get_master_name(master_id)
            
            original_text = query.message.caption if query.message.photo else query.message.text
            base_text = original_text.split('\n\n✅')[0].split('\n\n⚠️')[0].split('\n\n👷')[0].split('\n\n❌')[0]
            
            assigned_status_ru = STATUS_TRANSLATIONS.get('Assigned')

            await edit_message(f"{base_text}\n\n✅ Мастер назначен: *{master_name}* ({assigned_status_ru})")
            
        elif action == "cancel_assign":
            req_id = data[1]
            keyboard = [
                [InlineKeyboardButton('✅ В работу', callback_data=f'assign_menu:{req_id}')],
                [InlineKeyboardButton('❌ Отклонена', callback_data=f'status:Denied:{req_id}')],
            ]
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif action == "busy":
            await query.answer("⚠️ Этот мастер сейчас занят", show_alert=True)
    except Exception as e:
        print(f"Error in button_handler: {e}")

def start_background_bot_loop():
    """Runs the Telegram bot in a dedicated background thread with a permanent event loop."""
    global background_loop, telegram_app
    
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    background_loop = loop
    
    # Initialize the application inside this loop
    telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    
    # Initialize and start the bot
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    
    print("🤖 Telegram Bot initialized in background loop")
    
    # Run the loop forever to process updates
    loop.run_forever()

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Handle incoming Telegram updates via webhook"""
    if telegram_app and background_loop:
        # Pass the update to the background loop safely
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), background_loop)
    return 'OK'

if __name__ == '__main__':
    # Start the bot background thread
    bot_thread = threading.Thread(target=start_background_bot_loop, daemon=True)
    bot_thread.start()
    
    # Wait a moment for bot to initialize
    time.sleep(2)
    
    # Set webhook on startup
    webhook_url = os.getenv('WEBHOOK_URL', 'https://qualitycontrol-api.onrender.com/telegram-webhook')
    
    if TELEGRAM_BOT_TOKEN:
        try:
            # Delete any existing webhook first
            http_requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook')
            # Set new webhook
            response = http_requests.post(
                f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook',
                json={'url': webhook_url}
            )
            print(f"📡 Webhook set: {response.json()}")
        except Exception as e:
            print(f"⚠️ Failed to set webhook: {e}")
    
    app.run(host='0.0.0.0', port=8000, debug=False)
