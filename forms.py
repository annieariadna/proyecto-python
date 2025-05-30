
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(2,20)])
    email = StringField('Correo', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(6,128)])
    confirm_password = PasswordField('Repite Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    email = StringField('Correo', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

class ReportForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    category = SelectField('Categoría', choices=[('lost','Perdido'), ('found','Encontrado')])
    location = StringField('Ubicación', validators=[Optional(), Length(max=100)], 
                          render_kw={"placeholder": "Ej: Biblioteca, Cafetería, Aula 101"})
    image = FileField('Imagen (opcional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes JPG y PNG')])
    submit = SubmitField('Enviar reporte')

class SearchForm(FlaskForm):
    query = StringField('Buscar', validators=[Optional()], 
                       render_kw={"placeholder": "Buscar objetos..."})
    category = SelectField('Categoría', choices=[('', 'Todas'), ('lost','Perdidos'), ('found','Encontrados')])
    location = StringField('Ubicación', validators=[Optional()], 
                          render_kw={"placeholder": "Ubicación..."})
    submit = SubmitField('Buscar')