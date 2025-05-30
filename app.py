
from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory
from config import Config
from models import db, User, Report
from forms import RegistrationForm, LoginForm, ReportForm, SearchForm
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from PIL import Image 
import os
import secrets
from sqlalchemy import or_, and_

app = Flask(__name__)
app.config.from_object(Config)

# Configuración para subida de archivos
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crear directorio de uploads si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def save_picture(form_picture):
    """Guarda imagen redimensionada"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)
    
    # Redimensionar imagen
    img = Image.open(form_picture)
    img.thumbnail((800, 600))  # Máximo 800x600px
    img.save(picture_path, optimize=True, quality=85)
    
    return picture_fn

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_form = SearchForm()
    reports = Report.query.order_by(Report.date_posted.desc()).paginate(
        page=page, per_page=6, error_out=False)
    return render_template('index.html', reports=reports, search_form=search_form)

@app.route('/search')
def search():
    form = SearchForm()
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    
    # Construir consulta
    reports_query = Report.query
    
    if query:
        reports_query = reports_query.filter(
            or_(Report.title.contains(query), 
                Report.description.contains(query))
        )
    
    if category:
        reports_query = reports_query.filter(Report.category == category)
    
    if location:
        reports_query = reports_query.filter(Report.location.contains(location))
    
    reports = reports_query.order_by(Report.date_posted.desc()).paginate(
        page=page, per_page=6, error_out=False)
    
    return render_template('search.html', reports=reports, form=form,
                         query=query, category=category, location=location)

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data,
                    password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('¡Cuenta creada con éxito! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash(f'¡Bienvenido {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas. Verifica tu email y contraseña.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('index'))

@app.route('/report/new', methods=['GET','POST'])
@login_required
def new_report():
    form = ReportForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = save_picture(form.image.data)
        
        report = Report(title=form.title.data,
                        description=form.description.data,
                        category=form.category.data,
                        location=form.location.data,
                        image_filename=image_filename,
                        author=current_user)
        db.session.add(report)
        db.session.commit()
        flash('¡Reporte enviado exitosamente!', 'success')
        return redirect(url_for('index'))
    return render_template('report.html', form=form)

@app.route('/report/<int:report_id>')
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    return render_template('item_detail.html', report=report)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/my-reports')
@login_required
def my_reports():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(user_id=current_user.id).order_by(
        Report.date_posted.desc()).paginate(page=page, per_page=5, error_out=False)
    return render_template('my_reports.html', reports=reports)

@app.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.author != current_user:
        flash('No tienes permisos para eliminar este reporte.', 'danger')
        return redirect(url_for('index'))
    
    # Eliminar imagen si existe
    if report.image_filename:
        image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], report.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(report)
    db.session.commit()
    flash('Reporte eliminado exitosamente.', 'success')
    return redirect(url_for('my_reports'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

