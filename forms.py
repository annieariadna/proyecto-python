
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(2,20)],
                          render_kw={"placeholder": "Tu nombre de usuario"})
    email = StringField('Correo institucional', validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "usuario@utp.edu.pe"})
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(6,128)],
                            render_kw={"placeholder": "Mínimo 6 caracteres"})
    confirm_password = PasswordField('Confirmar Contraseña', 
                                   validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')],
                                   render_kw={"placeholder": "Repite tu contraseña"})
    submit = SubmitField('Registrarse')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está ocupado. Elige otro.')
    
    def validate_email(self, email):
        if not email.data.endswith('@utp.edu.pe'):
            raise ValidationError('Debes usar tu correo institucional UTP (@utp.edu.pe)')
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese correo ya está registrado. ¿Ya tienes cuenta?')

class LoginForm(FlaskForm):
    email = StringField('Correo institucional', validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "usuario@utp.edu.pe"})
    password = PasswordField('Contraseña', validators=[DataRequired()],
                            render_kw={"placeholder": "Tu contraseña"})
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class ReportForm(FlaskForm):
    title = StringField('Título del objeto', validators=[DataRequired(), Length(max=100)],
                       render_kw={"placeholder": "Ej: iPhone 13 azul, Llaves con llavero UTP"})
    description = TextAreaField('Descripción detallada', validators=[DataRequired()],
                               render_kw={"placeholder": "Describe el objeto: características, dónde se perdió o encontró, etc.", "rows": 4})
    category = SelectField('Estado', choices=[('lost','Perdido'), ('found','Encontrado')],
                          validators=[DataRequired()])
    location = StringField('Ubicación', validators=[Optional(), Length(max=100)], 
                          render_kw={"placeholder": "Ej: Biblioteca, Cafetería, Aula 205"})
    image = FileField('Imagen del objeto (opcional)', 
                     validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes JPG, PNG y JPEG')])
    submit = SubmitField('Publicar reporte')

class SearchForm(FlaskForm):
    query = StringField('Buscar', validators=[Optional()], 
                       render_kw={"placeholder": "Describe el objeto que buscas..."})
    category = SelectField('Estado', choices=[('', 'Todos'), ('lost','Perdidos'), ('found','Encontrados')])
    location = StringField('Ubicación', validators=[Optional()], 
                          render_kw={"placeholder": "Ej: Biblioteca, Cafetería..."})
    submit = SubmitField('Buscar')

class ContactForm(FlaskForm):
    message = TextAreaField('Tu mensaje', validators=[DataRequired(), Length(min=10, max=500)],
                           render_kw={"placeholder": "Describe por qué contactas a este usuario...", "rows": 4})
    contact_email = StringField('Tu correo de contacto', validators=[DataRequired(), Email()],
                               render_kw={"placeholder": "tu.correo@utp.edu.pe"})
    submit = SubmitField('Enviar mensaje')
