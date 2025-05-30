
from flask import Flask, render_template, url_for, flash, redirect, request
from config import Config
from models import db, User, Report
from forms import RegistrationForm, LoginForm, ReportForm
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.order_by(Report.date_posted.desc())                             .paginate(page=page, per_page=5)
    return render_template('index.html', reports=reports)

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
        flash('Cuenta creada con éxito.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/report/new', methods=['GET','POST'])
@login_required
def new_report():
    form = ReportForm()
    if form.validate_on_submit():
        report = Report(title=form.title.data,
                        description=form.description.data,
                        category=form.category.data,
                        author=current_user)
        db.session.add(report)
        db.session.commit()
        flash('Reporte enviado.', 'success')
        return redirect(url_for('index'))
    return render_template('report.html', form=form)

@app.route('/report/<int:report_id>')
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    return render_template('item_detail.html', report=report)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

