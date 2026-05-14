import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cvisual.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'cvisual-secret-2025'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)

CVISUAL_MAILER_KEY = os.environ.get("CVISUAL_MAILER_KEY", "your_fallback_key_here")

# --- Models ---

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))
    image = db.Column(db.String(255))
    features = db.Column(db.Text)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    main_image = db.Column(db.String(255), nullable=False)
    challenge = db.Column(db.Text)
    solution = db.Column(db.Text)
    live_link = db.Column(db.String(255))
    gallery = db.Column(db.Text)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.String(255))

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='actualite')
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%d %b %Y"))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(255))

class Stat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.String(50))

class RecruitmentQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), default='text') # text, select, checkbox
    options = db.Column(db.Text) # Comma separated
    required = db.Column(db.Boolean, default=True)

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(50))
    tiktok = db.Column(db.String(100))
    sales_level = db.Column(db.String(50))
    cv_filename = db.Column(db.String(255))
    cv_link = db.Column(db.String(255))
    motivation = db.Column(db.Text)
    answers = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helpers ---

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_brevo_email(to_email, to_name, subject, html_content):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"accept": "application/json", "api-key": CVISUAL_MAILER_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "CVisual Agency", "email": "contact@cvisual.agency"},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 201
    except: return False

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify(error=str(e)), 500

# --- Routes ---

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data: return jsonify(msg="Missing JSON"), 400
    admin = Admin.query.filter_by(username=data.get('username')).first()
    if admin and check_password_hash(admin.password, data.get('password')):
        return jsonify(access_token=create_access_token(identity=admin.username)), 200
    return jsonify(msg="Identifiants invalides"), 401

@app.route('/api/services', methods=['GET'])
def get_services():
    items = Service.query.all()
    return jsonify([{'id':i.id, 'title':i.title, 'description':i.description, 'icon':i.icon} for i in items])

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    items = Project.query.all()
    return jsonify([{'id':i.id, 'title':i.title, 'category':i.category, 'main_image':i.main_image} for i in items])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    items = Stat.query.all()
    return jsonify({i.key: i.value for i in items})

@app.route('/api/news', methods=['GET'])
def get_news():
    items = News.query.order_by(News.id.desc()).all()
    return jsonify([{'id':i.id, 'title':i.title, 'content':i.content, 'type':i.type, 'date':i.date} for i in items])

@app.route('/api/clients', methods=['GET'])
def get_clients():
    items = Client.query.all()
    return jsonify([{'id':i.id, 'name':i.name, 'logo':i.logo} for i in items])

@app.route('/api/newsletter', methods=['POST'])
def subscribe():
    data = request.json
    if not data.get('email'): return jsonify(error="Email requis"), 400
    if not Newsletter.query.filter_by(email=data['email']).first():
        db.session.add(Newsletter(email=data['email']))
        db.session.commit()
    return jsonify(success=True)

@app.route('/api/recruitment/questions', methods=['GET'])
def get_questions():
    qs = RecruitmentQuestion.query.all()
    return jsonify([{'id': q.id, 'question': q.question, 'type': q.type, 'options': q.options, 'required': q.required} for q in qs])

@app.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    new_app = Application(
        full_name=data.get('fullName'), email=data.get('email'), whatsapp=data.get('whatsapp'),
        tiktok=data.get('tiktok'), sales_level=data.get('salesLevel'), cv_link=data.get('cvLink'),
        cv_filename=data.get('cvFilename'), motivation=data.get('motivation'), answers=data.get('answers')
    )
    db.session.add(new_app)
    db.session.commit()
    return jsonify(success=True), 201

@app.route('/api/apply/upload', methods=['POST'])
def upload_cv():
    if 'file' not in request.files: return jsonify(error="No file"), 400
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify(filename=filename, success=True)
    return jsonify(error="Invalid file"), 400

# --- Admin Protected ---

@app.route('/api/admin/newsletter', methods=['GET'])
@jwt_required()
def admin_newsletter():
    items = Newsletter.query.order_by(Newsletter.date.desc()).all()
    return jsonify([{'id':i.id, 'email':i.email, 'date':i.date.strftime("%d %b %Y")} for i in items])

@app.route('/api/admin/clients', methods=['POST'])
@jwt_required()
def admin_add_client():
    data = request.json
    db.session.add(Client(name=data['name'], logo=data['logo']))
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/admin/clients/<int:id>', methods=['DELETE'])
@jwt_required()
def admin_del_client(id):
    item = Client.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/admin/recruitment/questions', methods=['POST'])
@jwt_required()
def admin_add_question():
    data = request.json
    db.session.add(RecruitmentQuestion(question=data['question'], type=data.get('type','text'), options=data.get('options'), required=data.get('required',True)))
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def admin_apps():
    items = Application.query.order_by(Application.date.desc()).all()
    return jsonify([{
        'id':a.id, 'full_name':a.full_name, 'email':a.email, 'status':a.status, 'date':a.date.strftime("%d %b %Y"),
        'cv_filename': a.cv_filename, 'cv_link': a.cv_link
    } for a in items])

# Init
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        db.session.add(Admin(username='admin', password=generate_password_hash('admin123')))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
