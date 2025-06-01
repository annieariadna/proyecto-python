
from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory, jsonify
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
from datetime import datetime

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
    
    # Obtener parámetros de filtro
    category_filter = request.args.get('category', '')
    location_filter = request.args.get('location', '')
    query_filter = request.args.get('query', '')
    
    # Construir consulta base
    reports_query = Report.query
    
    # Aplicar filtros si existen
    if category_filter:
        reports_query = reports_query.filter(Report.category == category_filter)
    
    if location_filter:
        reports_query = reports_query.filter(Report.location.ilike(f'%{location_filter}%'))
    
    if query_filter:
        reports_query = reports_query.filter(
            or_(Report.title.ilike(f'%{query_filter}%'), 
                Report.description.ilike(f'%{query_filter}%'))
        )
    
    reports = reports_query.order_by(Report.date_posted.desc()).paginate(
        page=page, per_page=8, error_out=False)
    
    return render_template('index.html', reports=reports, search_form=search_form,
                         current_category=category_filter, current_location=location_filter, 
                         current_query=query_filter)

@app.route('/search')
def search():
    form = SearchForm()
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '')
    location = request.args.get('location', '').strip()
    page = request.args.get('page', 1, type=int)
    
    # Construir consulta
    reports_query = Report.query
    
    if query:
        reports_query = reports_query.filter(
            or_(Report.title.ilike(f'%{query}%'), 
                Report.description.ilike(f'%{query}%'))
        )
    
    if category and category != 'all':
        reports_query = reports_query.filter(Report.category == category)
    
    if location:
        reports_query = reports_query.filter(Report.location.ilike(f'%{location}%'))
    
    reports = reports_query.order_by(Report.date_posted.desc()).paginate(
        page=page, per_page=8, error_out=False)
    
    return render_template('search.html', reports=reports, form=form,
                         query=query, category=category, location=location)

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Validar que el email sea institucional UTP
        if not form.email.data.endswith('@utp.edu.pe'):
            flash('Debes usar tu correo institucional UTP (@utp.edu.pe)', 'danger')
            return render_template('register.html', form=form)
        
        # Verificar si ya existe el usuario
        existing_user = User.query.filter(
            or_(User.email == form.email.data, User.username == form.username.data)
        ).first()
        
        if existing_user:
            flash('El usuario o correo ya están registrados.', 'danger')
            return render_template('register.html', form=form)
        
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
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'¡Bienvenido {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas. Verifica tu email y contraseña.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
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
            try:
                image_filename = save_picture(form.image.data)
            except Exception as e:
                flash('Error al procesar la imagen. Inténtalo de nuevo.', 'danger')
                return render_template('report.html', form=form)
        
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

@app.route('/report/<int:report_id>/edit', methods=['GET','POST'])
@login_required
def edit_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.author != current_user:
        flash('No tienes permisos para editar este reporte.', 'danger')
        return redirect(url_for('index'))
    
    form = ReportForm()
    if form.validate_on_submit():
        report.title = form.title.data
        report.description = form.description.data
        report.category = form.category.data
        report.location = form.location.data
        
        if form.image.data:
            # Eliminar imagen anterior si existe
            if report.image_filename:
                old_image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], report.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            try:
                report.image_filename = save_picture(form.image.data)
            except Exception as e:
                flash('Error al procesar la imagen. El reporte se guardó sin imagen.', 'warning')
        
        db.session.commit()
        flash('Reporte actualizado exitosamente.', 'success')
        return redirect(url_for('report_detail', report_id=report.id))
    
    elif request.method == 'GET':
        form.title.data = report.title
        form.description.data = report.description
        form.category.data = report.category
        form.location.data = report.location
    
    return render_template('report.html', form=form, is_edit=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/my-reports')
@login_required
def my_reports():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(user_id=current_user.id).order_by(
        Report.date_posted.desc()).paginate(page=page, per_page=6, error_out=False)
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

@app.route('/contact/<int:report_id>', methods=['POST'])
@login_required
def contact_user(report_id):
    """Endpoint para manejar contacto entre usuarios"""
    report = Report.query.get_or_404(report_id)
    message = request.form.get('message', '').strip()
    contact_email = request.form.get('contact_email', '').strip()
    
    if not message or not contact_email:
        flash('Debes completar todos los campos.', 'danger')
        return redirect(url_for('report_detail', report_id=report_id))
    
    # Aquí podrías implementar el envío de email real
    # Por ahora solo mostramos mensaje de éxito
    flash(f'Mensaje enviado a {report.author.username}. Te contactará pronto.', 'success')
    return redirect(url_for('report_detail', report_id=report_id))

# API endpoints para funcionalidad AJAX
@app.route('/api/reports')
def api_reports():
    """API endpoint para obtener reportes filtrados"""
    category = request.args.get('category', '')
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    
    reports_query = Report.query
    
    if category and category != 'all':
        reports_query = reports_query.filter(Report.category == category)
    
    if query:
        reports_query = reports_query.filter(
            or_(Report.title.ilike(f'%{query}%'), 
                Report.description.ilike(f'%{query}%'))
        )
    
    if location:
        reports_query = reports_query.filter(Report.location.ilike(f'%{location}%'))
    
    reports = reports_query.order_by(Report.date_posted.desc()).paginate(
        page=page, per_page=8, error_out=False)
    
    reports_data = []
    for report in reports.items:
        reports_data.append({
            'id': report.id,
            'title': report.title,
            'description': report.description[:150] + '...' if len(report.description) > 150 else report.description,
            'category': report.category,
            'location': report.location or 'No especificada',
            'date': report.date_posted.strftime('%d/%m/%Y'),
            'author': report.author.username,
            'image': url_for('uploaded_file', filename=report.image_filename) if report.image_filename else None,
            'detail_url': url_for('report_detail', report_id=report.id)
        })
    
    return jsonify({
        'reports': reports_data,
        'has_next': reports.has_next,
        'has_prev': reports.has_prev,
        'page': reports.page,
        'pages': reports.pages,
        'total': reports.total
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(error):
    flash('El archivo es demasiado grande. Máximo 16MB.', 'danger')
    return redirect(request.url)

# Context processors para templates
@app.context_processor
def utility_processor():
    def format_datetime(dt):
        return dt.strftime('%d/%m/%Y %H:%M')
    
    def get_icon_for_item(title):
        """Retorna icono Font Awesome basado en el título del objeto"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['telefono', 'celular', 'movil', 'iphone', 'samsung']):
            return 'fas fa-mobile-alt'
        elif any(word in title_lower for word in ['laptop', 'computadora', 'pc']):
            return 'fas fa-laptop'
        elif any(word in title_lower for word in ['llave', 'llaves']):
            return 'fas fa-key'
        elif any(word in title_lower for word in ['libro', 'cuaderno', 'texto']):
            return 'fas fa-book'
        elif any(word in title_lower for word in ['mochila', 'bolso', 'cartera']):
            return 'fas fa-shopping-bag'
        elif any(word in title_lower for word in ['audifonos', 'auriculares']):
            return 'fas fa-headphones'
        elif any(word in title_lower for word in ['reloj']):
            return 'fas fa-clock'
        elif any(word in title_lower for word in ['calculadora']):
            return 'fas fa-calculator'
        else:
            return 'fas fa-question-circle'
    
    return dict(format_datetime=format_datetime, get_icon_for_item=get_icon_for_item)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)