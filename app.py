import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'cvisual.db'))
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'cvisual-secret-2025')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
jwt = JWTManager(app)

CVISUAL_MAILER_KEY = os.environ.get("CVISUAL_MAILER_KEY", "your_fallback_key_here")

# --- Models ---

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(100)) # Optional for business accounts
    is_company = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class RecruitmentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(200), nullable=False)
    job_details = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(100)) # Session based for non-logged in
    sender = db.Column(db.String(50)) # 'visitor' or 'admin'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    image = db.Column(db.Text)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    main_image = db.Column(db.Text)
    challenge = db.Column(db.Text)
    solution = db.Column(db.Text)
    live_link = db.Column(db.String(255))

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='actualite')
    image = db.Column(db.Text)
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%d %b %Y"))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.Text)

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class RecruitmentQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), default='text')
    options = db.Column(db.Text)
    required = db.Column(db.Boolean, default=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer) # Related to User if logged in
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(50))
    tiktok = db.Column(db.String(100))
    cv_filename = db.Column(db.String(255))
    cv_link = db.Column(db.String(255))
    motivation = db.Column(db.Text)
    answers = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)
class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    service = db.Column(db.String(100))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    variables = db.Column(db.String(255))

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

def send_templated_email(to_email, template_key, context):
    try:
        template = EmailTemplate.query.filter_by(key=template_key).first()
        if not template:
            print(f"Modele d'email non trouve pour la cle : {template_key}")
            return False
        
        logo_setting = Setting.query.filter_by(key='logo_url').first()
        logo_url = logo_setting.value if logo_setting else "https://cvisual-backend.onrender.com/api/uploads/logo.jpg"
        
        full_context = {
            'logo_url': logo_url,
            **context
        }
        
        subject = template.subject
        body = template.body
        
        for k, v in full_context.items():
            subject = subject.replace(f"{{{k}}}", str(v if v is not None else ''))
            body = body.replace(f"{{{k}}}", str(v if v is not None else ''))
            
        return send_brevo_email(to_email, subject, body)
    except Exception as e:
        print(f"Erreur envoi email templated: {e}")
        return False

def send_brevo_email(to_email, subject, html_content):
    api_key = os.environ.get('CVISUAL_MAILER_KEY') or os.environ.get('BREVO_API_KEY')
    if not api_key:
        print("BREVO_API_KEY / CVISUAL_MAILER_KEY non configurée - Email non envoyé")
        return False
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "CVisual Agency", "email": "cvisualht1@gmail.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Email response status: {response.status_code}")
        if response.status_code != 201:
            print(f"Email error response: {response.text}")
        return response.status_code == 201
    except Exception as e:
        print(f"Erreur Email: {e}")
        return False

# --- Routes ---

@app.route('/api/track', methods=['POST'])
def track_visitor():
    v = Visitor(ip_address=request.remote_addr, user_agent=request.user_agent.string)
    db.session.add(v); db.session.commit()
    return jsonify(success=True)

@app.route('/api/user/register', methods=['POST'])
def user_register():
    d = request.json
    if User.query.filter_by(email=d['email']).first():
        return jsonify(msg="Email déjà utilisé"), 400
    u = User(
        full_name=d['fullName'],
        email=d['email'],
        password=generate_password_hash(d['password']),
        company_name=d.get('companyName'),
        is_company=d.get('isCompany', False)
    )
    db.session.add(u); db.session.commit()
    
    # Send welcome email using templates
    send_templated_email(u.email, 'user_registered', {'full_name': u.full_name, 'email': u.email})
    
    return jsonify(success=True)

@app.route('/api/user/login', methods=['POST'])
def user_login():
    d = request.json
    u = User.query.filter_by(email=d.get('email')).first()
    if u and check_password_hash(u.password, d.get('password')):
        # Send security login email alert
        send_templated_email(u.email, 'user_login', {
            'full_name': u.full_name,
            'email': u.email,
            'date': datetime.now().strftime("%d %b %Y %H:%M"),
            'ip_address': request.remote_addr
        })
        return jsonify(access_token=create_access_token(identity=u.email), user={'name': u.full_name, 'email': u.email}), 200
    return jsonify(msg="Invalide"), 401

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    admin = Admin.query.filter_by(username=data.get('username')).first()
    if admin and check_password_hash(admin.password, data.get('password')):
        return jsonify(access_token=create_access_token(identity=admin.username)), 200
    return jsonify(msg="Invalide"), 401

# Public Data
@app.route('/api/services', methods=['GET'])
def get_services():
    items = Service.query.all()
    return jsonify([{'id':i.id, 'title':i.title, 'description':i.description, 'icon':i.icon, 'image':i.image} for i in items])

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    items = Project.query.all()
    return jsonify([{
        'id': i.id,
        'title': i.title,
        'category': i.category,
        'main_image': i.main_image,
        'challenge': i.challenge,
        'solution': i.solution,
        'live_link': i.live_link
    } for i in items])

@app.route('/api/news', methods=['GET'])
def get_news():
    items = News.query.order_by(News.id.desc()).all()
    return jsonify([{'id':i.id, 'title':i.title, 'content':i.content, 'type':i.type, 'image':i.image, 'date':i.date} for i in items])

@app.route('/api/clients', methods=['GET'])
def get_clients():
    items = Client.query.all()
    return jsonify([{'id':i.id, 'name':i.name, 'logo':i.logo} for i in items])

@app.route('/api/recruitment/questions', methods=['GET'])
def get_questions():
    qs = RecruitmentQuestion.query.all()
    return jsonify([{'id': q.id, 'question': q.question, 'type': q.type, 'options': q.options, 'required': q.required} for q in qs])

@app.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    # Check if recruitment is open
    info = RecruitmentInfo.query.first()
    if info and not info.is_active:
        return jsonify(error="Le recrutement est fermé."), 403

    new_app = Application(
        full_name=data.get('fullName'),
        email=data.get('email'),
        whatsapp=data.get('whatsapp'),
        tiktok=data.get('tiktok'),
        cv_filename=data.get('cvFilename'),
        cv_link=data.get('cvLink'),
        motivation=data.get('motivation'),
        answers=data.get('answers')
    )
    db.session.add(new_app)
    db.session.commit()

    # Send Templated Email to Candidate
    send_templated_email(new_app.email, 'candidature_received', {
        'full_name': new_app.full_name,
        'whatsapp': new_app.whatsapp or 'Non renseigne',
        'tiktok': new_app.tiktok or 'Non renseigne'
    })

    # Send Premium Notification to Admin
    admin_html = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #f8fafc; color: #1e293b;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #0f172a; font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 800; margin: 0;">Nouvelle Candidature Reçue !</h2>
            <p style="color: #64748b; font-size: 14px; margin-top: 5px;">Un nouveau talent souhaite rejoindre CVisual Agency</p>
        </div>
        
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; padding: 30px; border-radius: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);">
            <h3 style="margin-top: 0; margin-bottom: 20px; font-size: 18px; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px;">Détails du candidat</h3>
            <table style="width: 100%; font-size: 15px; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 8px 0; color: #64748b; width: 140px; font-weight: 500;">Nom complet :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a;">{new_app.full_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Adresse email :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a;"><a href="mailto:{new_app.email}" style="color: #3b82f6; text-decoration: none;">{new_app.email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b; font-weight: 500;">WhatsApp :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a;">{new_app.whatsapp or 'Non renseigné'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b; font-weight: 500;">TikTok :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a;">{new_app.tiktok or 'Non renseigné'}</td>
                </tr>
            </table>
            
            <h4 style="margin-bottom: 8px; color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;">Message de motivation</h4>
            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 12px; font-size: 14px; line-height: 1.5; color: #334155; font-style: italic; margin-bottom: 25px;">
                "{new_app.motivation or 'Aucun message fourni'}"
            </div>
            
            <a href="https://cvisual-admin.vercel.app/pages/admin/applications.html" style="display: block; text-align: center; background-color: #0f172a; color: #ffffff; padding: 16px; border-radius: 14px; font-weight: 700; text-decoration: none; font-size: 16px;">Voir la candidature sur le Dashboard</a>
        </div>
    </div>
    """
    send_brevo_email("cvisualht1@gmail.com", "Nouvelle Candidature !", admin_html)

    return jsonify(success=True)

@app.route('/api/contact', methods=['POST'])
def contact():
    d = request.json
    inquiry = Inquiry(
        first_name=d.get('firstName'),
        last_name=d.get('lastName'),
        email=d.get('email'),
        service=d.get('service'),
        message=d.get('message')
    )
    db.session.add(inquiry)
    db.session.commit()

    # Send Premium Notification to Admin
    admin_html = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #f8fafc; color: #1e293b;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #0f172a; font-family: 'Outfit', sans-serif; font-size: 24px; font-weight: 800; margin: 0;">Nouveau Devis / Contact !</h2>
            <p style="color: #64748b; font-size: 14px; margin-top: 5px;">Un nouveau client potentiel a soumis une demande</p>
        </div>
        
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; padding: 30px; border-radius: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);">
            <h3 style="margin-top: 0; margin-bottom: 20px; font-size: 18px; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px;">Informations du contact</h3>
            <table style="width: 100%; font-size: 15px; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 8px 0; color: #64748b; width: 140px; font-weight: 500;">Nom complet :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a;">{inquiry.first_name} {inquiry.last_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Adresse email :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #0f172a;"><a href="mailto:{inquiry.email}" style="color: #3b82f6; text-decoration: none;">{inquiry.email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Service demandé :</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #10b981;">{inquiry.service}</td>
                </tr>
            </table>
            
            <h4 style="margin-bottom: 8px; color: #64748b; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;">Message / Besoin du client</h4>
            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 12px; font-size: 14px; line-height: 1.5; color: #334155; font-style: italic; margin-bottom: 25px;">
                "{inquiry.message}"
            </div>
            
            <a href="https://cvisual-admin.vercel.app/pages/admin/inbox.html" style="display: block; text-align: center; background-color: #0f172a; color: #ffffff; padding: 16px; border-radius: 14px; font-weight: 700; text-decoration: none; font-size: 16px;">Consulter la boîte de réception</a>
        </div>
    </div>
    """
    send_brevo_email("cvisualht1@gmail.com", "Nouveau Message de Contact !", admin_html)

    # Send Templated Email to Client
    send_templated_email(inquiry.email, 'devis_received', {
        'first_name': inquiry.first_name,
        'service': inquiry.service,
        'message': inquiry.message
    })

    return jsonify(success=True)

# Admin CRUD
@app.route('/api/apply/upload', methods=['POST'])
def apply_upload():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        name = secure_filename(f"cv_{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], name))
        return jsonify(success=True, filename=name)
    return jsonify(error="Fichier non valide"), 400

@app.route('/api/admin/upload', methods=['POST'])
@jwt_required()
def upload():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        import base64
        file_bytes = file.read()
        mime_type = file.mimetype or "image/png"
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        base64_url = f"data:{mime_type};base64,{base64_encoded}"
        return jsonify(success=True, url=base64_url)
    return jsonify(error="Error"), 400

@app.route('/api/admin/services', methods=['POST'])
@app.route('/api/admin/services/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_services(id=None):
    if request.method == 'POST':
        d = request.json
        s = Service(title=d['title'], description=d.get('description'), icon=d.get('icon'), image=d.get('image'))
        db.session.add(s); db.session.commit(); return jsonify(success=True)
    item = Service.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    d = request.json
    item.title = d['title']; item.description = d.get('description'); item.icon = d.get('icon'); item.image = d.get('image')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/portfolio', methods=['POST'])
@app.route('/api/admin/portfolio/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_portfolio(id=None):
    if request.method == 'POST':
        d = request.json
        p = Project(
            title=d['title'],
            category=d['category'],
            main_image=d.get('main_image'),
            challenge=d.get('challenge'),
            solution=d.get('solution'),
            live_link=d.get('live_link')
        )
        db.session.add(p); db.session.commit(); return jsonify(success=True)
    item = Project.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    d = request.json
    item.title = d['title']
    item.category = d['category']
    item.main_image = d.get('main_image')
    item.challenge = d.get('challenge')
    item.solution = d.get('solution')
    item.live_link = d.get('live_link')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/news', methods=['POST'])
@app.route('/api/admin/news/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_news(id=None):
    if request.method == 'POST':
        d = request.json
        n = News(title=d['title'], content=d['content'], type=d.get('type'), image=d.get('image'))
        db.session.add(n); db.session.commit(); return jsonify(success=True)
    item = News.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    d = request.json
    item.title = d['title']; item.content = d['content']; item.type = d.get('type'); item.image = d.get('image')
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/clients', methods=['POST'])
@app.route('/api/admin/clients/<int:id>', methods=['DELETE'])
@jwt_required()
def admin_clients(id=None):
    if request.method == 'POST':
        d = request.json
        db.session.add(Client(name=d['name'], logo=d.get('logo'))); db.session.commit(); return jsonify(success=True)
    item = Client.query.get_or_404(id)
    db.session.delete(item); db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def admin_apps():
    items = Application.query.order_by(Application.date.desc()).all()
    return jsonify([{'id':a.id, 'full_name':a.full_name, 'email':a.email, 'status':a.status, 'date':a.date.strftime("%d %b %Y")} for a in items])

@app.route('/api/admin/applications/<int:id>', methods=['GET'])
@jwt_required()
def admin_app_detail(id):
    a = Application.query.get_or_404(id)
    return jsonify({
        'id': a.id,
        'full_name': a.full_name,
        'email': a.email,
        'whatsapp': a.whatsapp,
        'tiktok': a.tiktok,
        'cv_filename': a.cv_filename,
        'cv_link': a.cv_link,
        'motivation': a.motivation,
        'answers': a.answers,
        'status': a.status,
        'date': a.date.strftime("%d %b %Y %H:%M")
    })

@app.route('/api/admin/inquiries', methods=['GET'])
@jwt_required()
def admin_inquiries_list():
    items = Inquiry.query.order_by(Inquiry.date.desc()).all()
    return jsonify([{
        'id': i.id,
        'name': f"{i.first_name} {i.last_name}",
        'email': i.email,
        'service': i.service,
        'status': i.status,
        'date': i.date.strftime("%d %b %Y")
    } for i in items])

@app.route('/api/admin/inquiries/<int:id>', methods=['GET', 'DELETE', 'PUT'])
@jwt_required()
def admin_inquiry_detail(id):
    i = Inquiry.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(i); db.session.commit(); return jsonify(success=True)
    if request.method == 'PUT':
        i.status = request.json.get('status', i.status)
        db.session.commit(); return jsonify(success=True)
    return jsonify({
        'id': i.id,
        'firstName': i.first_name,
        'lastName': i.last_name,
        'email': i.email,
        'service': i.service,
        'message': i.message,
        'status': i.status,
        'date': i.date.strftime("%d %b %Y %H:%M")
    })

@app.route('/api/admin/applications/<int:id>/status', methods=['PUT'])
@jwt_required()
def admin_app_status(id):
    item = Application.query.get_or_404(id)
    status = request.json.get('status')
    item.status = status
    db.session.commit()

    # Send status email notification using dynamic template engine
    if status in ['accepted', 'interview', 'rejected'] and item.email:
        template_key = f"candidature_{status}"
        send_templated_email(item.email, template_key, {
            'full_name': item.full_name,
            'whatsapp': item.whatsapp or 'Non renseigne'
        })

    return jsonify(success=True)

@app.route('/api/admin/recruitment/questions', methods=['POST'])
@app.route('/api/admin/recruitment/questions/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_questions(id=None):
    if request.method == 'POST':
        d = request.json
        q = RecruitmentQuestion(question=d['question'], type=d.get('type'), options=d.get('options'), required=d.get('required', False))
        db.session.add(q); db.session.commit(); return jsonify(success=True)
    
    item = RecruitmentQuestion.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item); db.session.commit(); return jsonify(success=True)
    
    d = request.json
    item.question = d['question']
    item.type = d.get('type')
    item.options = d.get('options')
    item.required = d.get('required', False)
    db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/newsletter', methods=['GET'])
@jwt_required()
def admin_newsletter():
    items = Newsletter.query.all()
    return jsonify([{'id':i.id, 'email':i.email, 'date':i.date.strftime("%d %b %Y")} for i in items])

# Chat
@app.route('/api/chat/messages', methods=['GET', 'POST'])
def chat_messages():
    v_id = request.args.get('visitor_id') or request.remote_addr
    if request.method == 'POST':
        d = request.json
        m = ChatMessage(visitor_id=v_id, sender=d['sender'], message=d['message'])
        db.session.add(m); db.session.commit(); return jsonify(success=True)
    msgs = ChatMessage.query.filter_by(visitor_id=v_id).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify([{'sender':m.sender, 'message':m.message, 'time':m.timestamp.strftime("%H:%M")} for m in msgs])

@app.route('/api/admin/chat/conversations', methods=['GET'])
@jwt_required()
def admin_chat_convs():
    # Group by visitor_id
    convs = db.session.query(ChatMessage.visitor_id).distinct().all()
    return jsonify([c[0] for c in convs])

# Stats & Settings
@app.route('/api/stats', methods=['GET'])
def get_stats():
    # Public stats
    return jsonify({
        'projects': Project.query.count(),
        'clients': Client.query.count(),
        'experience': 5, # Fallback
        'satisfaction': 99
    })

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    return jsonify({
        'visitors': Visitor.query.count(),
        'applications': Application.query.count(),
        'news': News.query.count(),
        'newsletter': Newsletter.query.count()
    })

@app.route('/api/admin/recruitment/info', methods=['GET', 'POST'])
@jwt_required()
def admin_recruitment_info():
    try:
        info = RecruitmentInfo.query.first()
        if request.method == 'POST':
            d = request.json
            if not info: info = RecruitmentInfo()
            info.job_title = d.get('job_title', '')
            info.job_details = d.get('job_details', '')
            db.session.add(info)
            db.session.commit()
            return jsonify(success=True)
        return jsonify({
            'job_title': info.job_title if info else '',
            'job_details': info.job_details if info else '',
            'is_active': info.is_active if info else True
        })
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/api/admin/recruitment/toggle', methods=['POST'])
@jwt_required()
def admin_recruitment_toggle():
    info = RecruitmentInfo.query.first()
    if not info: info = RecruitmentInfo(job_title="Poste à pourvoir")
    info.is_active = request.json.get('is_active', True)
    db.session.add(info); db.session.commit()
    return jsonify(success=True)

@app.route('/api/recruitment/info', methods=['GET'])
def get_recruitment_info():
    info = RecruitmentInfo.query.first()
    return jsonify({
        'job_title': info.job_title if info else '',
        'job_details': info.job_details if info else '',
        'is_active': info.is_active if info else True
    })

@app.route('/api/admin/manage', methods=['POST'])
@jwt_required()
def admin_manage():
    d = request.json
    if Admin.query.filter_by(username=d['username']).first():
        return jsonify(msg="Existe déjà"), 400
    new_admin = Admin(username=d['username'], password=generate_password_hash(d['password']))
    db.session.add(new_admin); db.session.commit(); return jsonify(success=True)

@app.route('/api/admin/emails/templates', methods=['GET'])
@jwt_required()
def admin_get_email_templates():
    tpls = EmailTemplate.query.order_by(EmailTemplate.id.asc()).all()
    return jsonify([{
        'id': t.id,
        'key': t.key,
        'name': t.name,
        'subject': t.subject,
        'body': t.body,
        'variables': t.variables
    } for t in tpls])

@app.route('/api/admin/emails/templates/<int:id>', methods=['GET', 'PUT'])
@jwt_required()
def admin_email_template_detail(id):
    tpl = EmailTemplate.query.get_or_404(id)
    if request.method == 'PUT':
        d = request.json
        tpl.subject = d.get('subject', tpl.subject)
        tpl.body = d.get('body', tpl.body)
        db.session.commit()
        return jsonify(success=True)
    return jsonify({
        'id': tpl.id,
        'key': tpl.key,
        'name': tpl.name,
        'subject': tpl.subject,
        'body': tpl.body,
        'variables': tpl.variables
    })

@app.route('/api/admin/emails/settings', methods=['GET', 'POST'])
@jwt_required()
def admin_email_settings():
    logo_setting = Setting.query.filter_by(key='logo_url').first()
    if not logo_setting:
        logo_setting = Setting(key='logo_url', value='https://cvisual-backend.onrender.com/api/uploads/logo.jpg')
        db.session.add(logo_setting)
        db.session.commit()
        
    if request.method == 'POST':
        d = request.json
        logo_setting.value = d.get('logo_url', logo_setting.value)
        db.session.commit()
        return jsonify(success=True)
        
    return jsonify({
        'logo_url': logo_setting.value
    })

@app.route('/api/admin/emails/broadcast', methods=['POST'])
@jwt_required()
def admin_email_broadcast():
    d = request.json
    target = d.get('target') # 'newsletter', 'applications', 'users'
    subject = d.get('subject')
    message = d.get('message')
    
    if not target or not subject or not message:
        return jsonify(error="Champs obligatoires manquants"), 400
        
    emails = []
    if target == 'newsletter':
        items = Newsletter.query.all()
        emails = [(i.email, 'Abonne') for i in items]
    elif target == 'applications':
        items = Application.query.all()
        seen = set()
        emails = []
        for i in items:
            if i.email and i.email not in seen:
                seen.add(i.email)
                emails.append((i.email, i.full_name or 'Candidat'))
    elif target == 'users':
        items = User.query.all()
        emails = [(i.email, i.full_name or 'Utilisateur') for i in items]
        
    sent_count = 0
    for to_email, full_name in emails:
        success = send_templated_email(to_email, 'broadcast', {
            'full_name': full_name,
            'message': message
        })
        if success:
            sent_count += 1
            
    return jsonify(success=True, sent_count=sent_count, total=len(emails))

# Init
with app.app_context():
    db.create_all()
    
    # Seed default settings
    if not Setting.query.filter_by(key='logo_url').first():
        db.session.add(Setting(key='logo_url', value='https://cvisual-backend.onrender.com/api/uploads/logo.jpg'))
        db.session.commit()

    # Seed default templates
    default_templates = [
        {
            'key': 'candidature_received',
            'name': 'Candidature Recue (Candidat)',
            'subject': 'Candidature Recue - CVisual Agency',
            'variables': 'full_name, whatsapp, tiktok, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #3b82f6; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0; tracking-tight: -0.025em;">Candidature Recue !</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous avons bien recu votre candidature pour rejoindre l'equipe creative de <b>CVisual Agency</b>. Nous vous remercions pour l'interet et la confiance que vous nous accordez.</p>
    
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">Recapitulatif de votre dossier</h4>
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr>
                <td style="padding: 6px 0; color: #64748b; width: 120px;">Nom complet :</td>
                <td style="padding: 6px 0; font-weight: 600;">{full_name}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b;">WhatsApp :</td>
                <td style="padding: 6px 0; font-weight: 600;">{whatsapp}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b;">TikTok :</td>
                <td style="padding: 6px 0; font-weight: 600;">{tiktok}</td>
            </tr>
        </table>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Notre equipe de recrutement va etudier votre profil avec la plus grande attention. Si vos competences et votre creativite correspondent a nos besoins actuels, nous vous contacterons tres prochainement pour planifier un entretien.</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous vous souhaitons une excellente journee et beaucoup de succes dans votre parcours.</p>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">
        Cordialement,<br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe CVisual Agency</span><br>
        <a href="mailto:cvisualht1@gmail.com" style="color: #3b82f6; text-decoration: none;">cvisualht1@gmail.com</a>
    </p>
</div>"""
        },
        {
            'key': 'candidature_accepted',
            'name': 'Candidature Acceptee (Candidat)',
            'subject': 'Felicitations ! Votre candidature est acceptee - CVisual Agency',
            'variables': 'full_name, whatsapp, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #10b981; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0; tracking-tight: -0.025em;">Felicitations ! 🎉</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous avons le plaisir de vous annoncer que votre candidature pour rejoindre <b>CVisual Agency</b> a ete retenue ! Votre profil et votre creativite ont grandement retenu l'attention de notre jury.</p>
    
    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #166534; letter-spacing: 0.05em;">Prochaines etapes pour votre Onboarding</h4>
        <p style="font-size: 14px; line-height: 1.6; color: #14532d; margin: 0;">
            1. Un responsable va vous ajouter au groupe d'onboarding officiel sur <b>WhatsApp</b>.<br>
            2. Vous recevrez les acces a vos outils de travail et votre contrat de collaboration.<br>
            3. Une reunion d'accueil (Kick-off) sera planifiee dans la semaine.
        </p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Si vous avez des questions urgentes, vous pouvez nous ecrire directement sur WhatsApp au numero associe a votre dossier ({whatsapp}).</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bienvenue dans l'aventure CVisual ! Ensemble, nous allons realiser de grandes choses.</p>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">
        Cordialement,<br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">La Direction - CVisual Agency</span><br>
        <a href="mailto:cvisualht1@gmail.com" style="color: #3b82f6; text-decoration: none;">cvisualht1@gmail.com</a>
    </p>
</div>"""
        },
        {
            'key': 'candidature_interview',
            'name': 'Invitation a un Entretien (Candidat)',
            'subject': 'Invitation a un entretien - CVisual Agency',
            'variables': 'full_name, whatsapp, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #3b82f6; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0; tracking-tight: -0.025em;">Invitation Entretien 📅</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Dans le cadre de l'etude de votre candidature chez <b>CVisual Agency</b>, nous avons le plaisir de vous inviter a un entretien individuel afin de faire plus ample connaissance et d'echanger sur votre parcours et votre creativite.</p>
    
    <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #1e3a8a; letter-spacing: 0.05em;">Modalites de l'entretien</h4>
        <p style="font-size: 14px; line-height: 1.6; color: #1e3a8a; margin: 0;">
            • <b>Format :</b> Visioconference (Google Meet / Zoom) ou Entretien telephonique<br>
            • <b>Duree :</b> Environ 20 a 30 minutes<br>
            • <b>Planification :</b> Un responsable du recrutement va vous contacter directement sur WhatsApp au <b>{whatsapp}</b> pour convenir d'un jour et d'une heure.
        </p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Veuillez s'il vous plait preparer une rapide presentation de vos plus belles realisations (portfolio, designs, videos ou strategies).</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous sommes impatients de discuter avec vous !</p>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">
        Cordialement,<br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe RH - CVisual Agency</span><br>
        <a href="mailto:cvisualht1@gmail.com" style="color: #3b82f6; text-decoration: none;">cvisualht1@gmail.com</a>
    </p>
</div>"""
        },
        {
            'key': 'candidature_rejected',
            'name': 'Candidature Non Retenue (Candidat)',
            'subject': 'Mise a jour concernant votre candidature - CVisual Agency',
            'variables': 'full_name, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #64748b; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0; tracking-tight: -0.025em;">Candidature non retenue</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous vous remercions sincerement pour le temps que vous avez accorde a soumettre votre dossier de candidature pour rejoindre <b>CVisual Agency</b>.</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bien que votre parcours soit tout a fait honorable, nous avons le regret de vous informer que nous n'avons pas pu retenir votre dossier pour les postes actuellement ouverts. Nous avons recu un tres grand nombre de candidatures tres qualifiees et les choix ont ete extremement difficiles.</p>
    
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <p style="font-size: 14px; line-height: 1.6; color: #475569; margin: 0;">
            ⚠️ <b>Note de notre vivier de talents :</b><br>
            Sauf avis contraire de votre part, nous conservons precieusement votre dossier dans notre base de donnees. Si de nouveaux besoins correspondant a votre profil se presentent a l'avenir, nous n'hesiterons pas a vous recontacter directement.
        </p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous vous souhaitons beaucoup de reussite dans la poursuite de votre carriere professionnelle.</p>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">
        Cordialement,<br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe RH - CVisual Agency</span><br>
        <a href="mailto:cvisualht1@gmail.com" style="color: #3b82f6; text-decoration: none;">cvisualht1@gmail.com</a>
    </p>
</div>"""
        },
        {
            'key': 'devis_received',
            'name': 'Accuse de reception de Devis (Client)',
            'subject': 'Demande de devis recue - CVisual Agency',
            'variables': 'first_name, service, message, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #3b82f6; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0; tracking-tight: -0.025em;">Demande Recue !</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{first_name}</b>,</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous vous remercions d'avoir contacte <b>CVisual Agency</b> pour votre projet. Nous avons bien recu votre demande de devis pour le service <b>{service}</b>.</p>
    
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">Details de votre message</h4>
        <p style="font-size: 14px; line-height: 1.5; color: #334155; font-style: italic; margin: 0;">
            "{message}"
        </p>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Un conseiller strategique de notre equipe etudie actuellement votre besoin et vous contactera sous 24 heures (jours ouvres) afin de vous proposer une offre sur mesure adaptee a vos objectifs.</p>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous sommes impatients de collaborer avec vous pour donner vie a vos projets les plus ambitieux !</p>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">
        Cordialement,<br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe CVisual Agency</span><br>
        <a href="mailto:cvisualht1@gmail.com" style="color: #3b82f6; text-decoration: none;">cvisualht1@gmail.com</a>
    </p>
</div>"""
        },
        {
            'key': 'user_registered',
            'name': 'Bienvenue sur CVisual (Utilisateur)',
            'subject': 'Bienvenue chez CVisual Agency !',
            'variables': 'full_name, email, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #3b82f6; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0;">Bienvenue !</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Nous sommes ravis de vous compter parmi nos membres enregistres ! Votre compte CVisual Agency a ete cree avec succes.</p>
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <table style="width: 100%; font-size: 14px;">
            <tr><td style="color: #64748b; width: 100px;">Adresse email :</td><td style="font-weight: 600;">{email}</td></tr>
            <tr><td style="color: #64748b;">Date d'inscription :</td><td style="font-weight: 600;">Aujourd'hui</td></tr>
        </table>
    </div>
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Vous pouvez desormais vous connecter a votre espace client pour suivre vos projets, consulter vos factures et echanger directement avec notre equipe.</p>
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">Cordialement,<br><span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe CVisual Agency</span></p>
</div>"""
        },
        {
            'key': 'user_login',
            'name': 'Alerte de Connexion (Utilisateur)',
            'subject': 'Nouvelle connexion detectee - CVisual Agency',
            'variables': 'full_name, email, date, ip_address, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #f59e0b; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0;">Securite du compte</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">Nouvelle connexion</p>
    </div>
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Une nouvelle connexion a ete detectee sur votre compte CVisual Agency.</p>
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 16px; margin-bottom: 30px;">
        <table style="width: 100%; font-size: 14px;">
            <tr><td style="color: #64748b; width: 120px;">Email :</td><td style="font-weight: 600;">{email}</td></tr>
            <tr><td style="color: #64748b;">Date & Heure :</td><td style="font-weight: 600;">{date}</td></tr>
            <tr><td style="color: #64748b;">Adresse IP :</td><td style="font-weight: 600;">{ip_address}</td></tr>
        </table>
    </div>
    <p style="font-size: 14px; color: #64748b; line-height: 1.5;">Si vous etes a l'origine de cette connexion, vous pouvez ignorer cet e-mail. Si vous ne reconnaissez pas cette activite, veuillez securiser votre compte et changer immediatement votre mot de passe.</p>
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">Cordialement,<br><span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe Securite CVisual</span></p>
</div>"""
        },
        {
            'key': 'broadcast',
            'name': 'Imel General (Diffusion)',
            'subject': 'Message Important - CVisual Agency',
            'variables': 'full_name, message, logo_url',
            'body': """<div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; border: 1px solid #e2e8f0; border-radius: 24px; background-color: #ffffff; color: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{logo_url}" alt="CVisual Logo" style="width: 70px; height: 70px; border-radius: 16px; margin-bottom: 15px; border: 1px solid #f1f5f9;">
        <h2 style="color: #3b82f6; font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0;">Annonce Importante</h2>
        <p style="color: #64748b; font-size: 14px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">CVisual Agency</p>
    </div>
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">Bonjour <b>{full_name}</b>,</p>
    <div style="font-size: 16px; line-height: 1.7; color: #334155; margin-bottom: 30px; white-space: pre-wrap;">{message}</div>
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    <p style="font-size: 14px; color: #64748b; line-height: 1.5; margin: 0; text-align: center;">Cordialement,<br><span style="font-size: 16px; font-weight: 700; color: #0f172a;">L'equipe CVisual Agency</span></p>
</div>"""
        }
    ]
    for dt in default_templates:
        if not EmailTemplate.query.filter_by(key=dt['key']).first():
            db.session.add(EmailTemplate(
                key=dt['key'],
                name=dt['name'],
                subject=dt['subject'],
                body=dt['body'],
                variables=dt['variables']
            ))
    db.session.commit()

    db.create_all()
    
    # Migrate password column size if needed
    try:
        with db.engine.connect() as conn:
            # Check and alter admin password column
            conn.execute(db.text("ALTER TABLE admin ALTER COLUMN password TYPE VARCHAR(255)"))
            conn.commit()
    except Exception as e:
        print(f"Admin password column migration: {e}")
    
    try:
        with db.engine.connect() as conn:
            # Check and alter user password column
            conn.execute(db.text("ALTER TABLE \"user\" ALTER COLUMN password TYPE VARCHAR(255)"))
            conn.commit()
    except Exception as e:
        print(f"User password column migration: {e}")
    
    if not Admin.query.filter_by(username='admin').first():
        db.session.add(Admin(username='admin', password=generate_password_hash('admin123')))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
