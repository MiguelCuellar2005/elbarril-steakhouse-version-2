from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import uuid
from dotenv import load_dotenv
from traducciones import traducir

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///elbarril.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg2://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

_requeridas = ['SECRET_KEY', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']
_faltantes = [v for v in _requeridas if not os.environ.get(v)]
if _faltantes:
    raise RuntimeError(f"Faltan variables de entorno en .env: {', '.join(_faltantes)}")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ── Modelos ───────────────────────────────────────────────────────────────────

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False, default='foodtruck')
    nombre_es = db.Column(db.String(100), nullable=False)
    nombre_en = db.Column(db.String(100))
    nombre_fr = db.Column(db.String(100))
    orden = db.Column(db.Integer, default=0)
    platos = db.relationship('Plato', backref='categoria', lazy=True)

    def nombre(self, idioma='es'):
        return getattr(self, f'nombre_{idioma}', None) or self.nombre_es


class Plato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    nombre_es = db.Column(db.String(150), nullable=False)
    nombre_en = db.Column(db.String(150))
    nombre_fr = db.Column(db.String(150))
    descripcion_es = db.Column(db.String(300))
    descripcion_en = db.Column(db.String(300))
    descripcion_fr = db.Column(db.String(300))
    precio = db.Column(db.Numeric(6, 2), nullable=False)
    imagen = db.Column(db.String(200))
    disponible = db.Column(db.Boolean, default=True)

    def nombre(self, idioma='es'):
        return getattr(self, f'nombre_{idioma}', None) or self.nombre_es

    def descripcion(self, idioma='es'):
        return getattr(self, f'descripcion_{idioma}', None) or self.descripcion_es


class Promocion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo_es = db.Column(db.String(150), nullable=False)
    titulo_en = db.Column(db.String(150))
    titulo_fr = db.Column(db.String(150))
    descripcion_es = db.Column(db.Text)
    descripcion_en = db.Column(db.Text)
    descripcion_fr = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)

    def titulo(self, idioma='es'):
        return getattr(self, f'titulo_{idioma}', None) or self.titulo_es

    def descripcion(self, idioma='es'):
        return getattr(self, f'descripcion_{idioma}', None) or self.descripcion_es

    def esta_activa(self):
        hoy = date.today()
        return self.fecha_inicio <= hoy <= self.fecha_fin


class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_evento = db.Column(db.String(150), nullable=False)
    ubicacion = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time)
    hora_fin = db.Column(db.Time)
    notas = db.Column(db.Text)


class SolicitudCatering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    fecha_evento = db.Column(db.Date)
    num_personas = db.Column(db.Integer)
    tipo_evento = db.Column(db.String(100))
    mensaje = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    atendida = db.Column(db.Boolean, default=False)


class Historia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto_es = db.Column(db.Text)
    texto_en = db.Column(db.Text)
    texto_fr = db.Column(db.Text)

    def texto(self, idioma='es'):
        return getattr(self, f'texto_{idioma}', None) or self.texto_es


class FotoGaleria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seccion = db.Column(db.String(20), nullable=False, default='galeria')
    imagen = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(255))
    orden = db.Column(db.Integer, default=0)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# ── Rutas públicas ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    hoy = date.today()

    promociones_activas = Promocion.query.filter(
        Promocion.fecha_inicio <= hoy,
        Promocion.fecha_fin >= hoy
    ).all()

    proximos_eventos = Evento.query.filter(
        Evento.fecha >= hoy
    ).order_by(Evento.fecha).limit(3).all()

    historia = Historia.query.first()
    fotos_historia = FotoGaleria.query.filter_by(seccion='historia').order_by(FotoGaleria.orden).all()

    return render_template(
        'index.html',
        promociones=promociones_activas,
        eventos=proximos_eventos,
        historia=historia,
        fotos_historia=fotos_historia
    )


@app.route('/menu')
def menu():
    categorias_foodtruck = Categoria.query.filter_by(tipo='foodtruck').order_by(Categoria.orden).all()
    categorias_resto = Categoria.query.filter_by(tipo='resto').order_by(Categoria.orden).all()
    return render_template(
        'menu.html',
        categorias_foodtruck=categorias_foodtruck,
        categorias_resto=categorias_resto
    )


@app.route('/galeria')
def galeria():
    fotos = FotoGaleria.query.filter_by(seccion='galeria').order_by(FotoGaleria.orden).all()
    return render_template('galeria.html', fotos=fotos)


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        fecha_evento_str = request.form.get('fecha_evento')
        fecha_evento = None
        if fecha_evento_str:
            fecha_evento = datetime.strptime(fecha_evento_str, '%Y-%m-%d').date()

        solicitud = SolicitudCatering(
            nombre=request.form.get('nombre'),
            telefono=request.form.get('telefono'),
            fecha_evento=fecha_evento,
            num_personas=request.form.get('num_personas') or None,
            tipo_evento=request.form.get('tipo_evento'),
            mensaje=request.form.get('mensaje')
        )
        db.session.add(solicitud)
        db.session.commit()
        flash('¡Gracias! Tu solicitud fue enviada, te contactaremos pronto.')
        return redirect(url_for('contacto'))

    return render_template('contacto.html')


@app.route('/idioma/<lang>')
def cambiar_idioma(lang):
    if lang in ('fr', 'en', 'es'):
        session['idioma'] = lang
    return redirect(request.referrer or url_for('index'))


@app.context_processor
def inject_idioma():
    idioma_actual = session.get('idioma', 'es')

    def t(clave):
        return traducir(clave, idioma_actual)

    return {'idioma': idioma_actual, 't': t}


# ── Autenticación ─────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')


@app.route('/admin/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ── Panel admin ───────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def dashboard():
    hoy = date.today()
    total_platos = Plato.query.count()
    promos_activas = Promocion.query.filter(
        Promocion.fecha_inicio <= hoy,
        Promocion.fecha_fin >= hoy
    ).count()
    proximos_eventos = Evento.query.filter(Evento.fecha >= hoy).count()
    catering_pendiente = SolicitudCatering.query.filter_by(atendida=False).count()

    return render_template(
        'dashboard.html',
        total_platos=total_platos,
        promos_activas=promos_activas,
        proximos_eventos=proximos_eventos,
        catering_pendiente=catering_pendiente
    )


# ── Utilidad para subir imágenes ──────────────────────────────────────────────

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'webp'}


def extension_permitida(nombre_archivo):
    return '.' in nombre_archivo and nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS


def guardar_imagen(archivo):
    if archivo and archivo.filename and extension_permitida(archivo.filename):
        extension = archivo.filename.rsplit('.', 1)[1].lower()
        nombre_unico = f"{uuid.uuid4().hex}.{extension}"
        ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
        archivo.save(ruta_completa)
        return nombre_unico
    return None


# ── CRUD Platos ───────────────────────────────────────────────────────────────

@app.route('/admin/platos')
@login_required
def admin_platos():
    categorias = Categoria.query.order_by(Categoria.orden).all()
    return render_template('admin_platos.html', categorias=categorias)


@app.route('/admin/platos/nuevo', methods=['GET', 'POST'])
@login_required
def plato_nuevo():
    categorias = Categoria.query.order_by(Categoria.orden).all()

    if request.method == 'POST':
        nombre_imagen = guardar_imagen(request.files.get('imagen'))

        plato = Plato(
            categoria_id=request.form.get('categoria_id'),
            nombre_es=request.form.get('nombre_es'),
            nombre_en=request.form.get('nombre_en'),
            nombre_fr=request.form.get('nombre_fr'),
            descripcion_es=request.form.get('descripcion_es'),
            descripcion_en=request.form.get('descripcion_en'),
            descripcion_fr=request.form.get('descripcion_fr'),
            precio=request.form.get('precio'),
            imagen=nombre_imagen,
            disponible=bool(request.form.get('disponible'))
        )
        db.session.add(plato)
        db.session.commit()
        flash('Plato agregado correctamente')
        return redirect(url_for('admin_platos'))

    return render_template('plato_form.html', categorias=categorias, plato=None)


@app.route('/admin/platos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def plato_editar(id):
    plato = Plato.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.orden).all()

    if request.method == 'POST':
        nombre_imagen = guardar_imagen(request.files.get('imagen'))
        if nombre_imagen:
            plato.imagen = nombre_imagen

        plato.categoria_id = request.form.get('categoria_id')
        plato.nombre_es = request.form.get('nombre_es')
        plato.nombre_en = request.form.get('nombre_en')
        plato.nombre_fr = request.form.get('nombre_fr')
        plato.descripcion_es = request.form.get('descripcion_es')
        plato.descripcion_en = request.form.get('descripcion_en')
        plato.descripcion_fr = request.form.get('descripcion_fr')
        plato.precio = request.form.get('precio')
        plato.disponible = bool(request.form.get('disponible'))
        db.session.commit()
        flash('Plato actualizado correctamente')
        return redirect(url_for('admin_platos'))

    return render_template('plato_form.html', categorias=categorias, plato=plato)


@app.route('/admin/platos/eliminar/<int:id>')
@login_required
def plato_eliminar(id):
    plato = Plato.query.get_or_404(id)
    db.session.delete(plato)
    db.session.commit()
    flash('Plato eliminado')
    return redirect(url_for('admin_platos'))


@app.route('/admin/platos/toggle/<int:id>')
@login_required
def plato_toggle(id):
    plato = Plato.query.get_or_404(id)
    plato.disponible = not plato.disponible
    db.session.commit()
    return redirect(url_for('admin_platos'))


# ── CRUD Promociones ──────────────────────────────────────────────────────────

@app.route('/admin/promociones')
@login_required
def admin_promociones():
    promociones = Promocion.query.order_by(Promocion.fecha_inicio.desc()).all()
    return render_template('admin_promociones.html', promociones=promociones)


@app.route('/admin/promociones/nueva', methods=['GET', 'POST'])
@login_required
def promocion_nueva():
    if request.method == 'POST':
        promo = Promocion(
            titulo_es=request.form.get('titulo_es'),
            titulo_en=request.form.get('titulo_en'),
            titulo_fr=request.form.get('titulo_fr'),
            descripcion_es=request.form.get('descripcion_es'),
            descripcion_en=request.form.get('descripcion_en'),
            descripcion_fr=request.form.get('descripcion_fr'),
            fecha_inicio=request.form.get('fecha_inicio'),
            fecha_fin=request.form.get('fecha_fin')
        )
        db.session.add(promo)
        db.session.commit()
        flash('Promoción creada')
        return redirect(url_for('admin_promociones'))

    return render_template('promocion_form.html', promocion=None)


@app.route('/admin/promociones/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def promocion_editar(id):
    promo = Promocion.query.get_or_404(id)

    if request.method == 'POST':
        promo.titulo_es = request.form.get('titulo_es')
        promo.titulo_en = request.form.get('titulo_en')
        promo.titulo_fr = request.form.get('titulo_fr')
        promo.descripcion_es = request.form.get('descripcion_es')
        promo.descripcion_en = request.form.get('descripcion_en')
        promo.descripcion_fr = request.form.get('descripcion_fr')
        promo.fecha_inicio = request.form.get('fecha_inicio')
        promo.fecha_fin = request.form.get('fecha_fin')
        db.session.commit()
        flash('Promoción actualizada')
        return redirect(url_for('admin_promociones'))

    return render_template('promocion_form.html', promocion=promo)


@app.route('/admin/promociones/eliminar/<int:id>')
@login_required
def promocion_eliminar(id):
    promo = Promocion.query.get_or_404(id)
    db.session.delete(promo)
    db.session.commit()
    flash('Promoción eliminada')
    return redirect(url_for('admin_promociones'))


# ── CRUD Eventos ──────────────────────────────────────────────────────────────

@app.route('/admin/eventos')
@login_required
def admin_eventos():
    eventos = Evento.query.order_by(Evento.fecha).all()
    return render_template('admin_eventos.html', eventos=eventos)


@app.route('/admin/eventos/nuevo', methods=['GET', 'POST'])
@login_required
def evento_nuevo():
    if request.method == 'POST':
        evento = Evento(
            nombre_evento=request.form.get('nombre_evento'),
            ubicacion=request.form.get('ubicacion'),
            fecha=request.form.get('fecha'),
            hora_inicio=request.form.get('hora_inicio') or None,
            hora_fin=request.form.get('hora_fin') or None,
            notas=request.form.get('notas')
        )
        db.session.add(evento)
        db.session.commit()
        flash('Evento creado')
        return redirect(url_for('admin_eventos'))

    return render_template('evento_form.html', evento=None)


@app.route('/admin/eventos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def evento_editar(id):
    evento = Evento.query.get_or_404(id)

    if request.method == 'POST':
        evento.nombre_evento = request.form.get('nombre_evento')
        evento.ubicacion = request.form.get('ubicacion')
        evento.fecha = request.form.get('fecha')
        evento.hora_inicio = request.form.get('hora_inicio') or None
        evento.hora_fin = request.form.get('hora_fin') or None
        evento.notas = request.form.get('notas')
        db.session.commit()
        flash('Evento actualizado')
        return redirect(url_for('admin_eventos'))

    return render_template('evento_form.html', evento=evento)


@app.route('/admin/eventos/eliminar/<int:id>')
@login_required
def evento_eliminar(id):
    evento = Evento.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento eliminado')
    return redirect(url_for('admin_eventos'))


# ── Catering ──────────────────────────────────────────────────────────────────

@app.route('/admin/catering')
@login_required
def admin_catering():
    solicitudes = SolicitudCatering.query.order_by(SolicitudCatering.fecha_creacion.desc()).all()
    return render_template('admin_catering.html', solicitudes=solicitudes)


@app.route('/admin/catering/toggle/<int:id>')
@login_required
def catering_toggle(id):
    solicitud = SolicitudCatering.query.get_or_404(id)
    solicitud.atendida = not solicitud.atendida
    db.session.commit()
    return redirect(url_for('admin_catering'))


@app.route('/admin/catering/eliminar/<int:id>')
@login_required
def catering_eliminar(id):
    solicitud = SolicitudCatering.query.get_or_404(id)
    db.session.delete(solicitud)
    db.session.commit()
    flash('Solicitud eliminada')
    return redirect(url_for('admin_catering'))


# ── Historia ──────────────────────────────────────────────────────────────────

@app.route('/admin/historia', methods=['GET', 'POST'])
@login_required
def admin_historia():
    hist = Historia.query.first()
    if not hist:
        hist = Historia(texto_es='', texto_en='', texto_fr='')
        db.session.add(hist)
        db.session.commit()

    if request.method == 'POST':
        hist.texto_es = request.form.get('texto_es')
        hist.texto_en = request.form.get('texto_en')
        hist.texto_fr = request.form.get('texto_fr')
        db.session.commit()
        flash('Historia actualizada')
        return redirect(url_for('admin_historia'))

    fotos = FotoGaleria.query.filter_by(seccion='historia').order_by(FotoGaleria.orden).all()
    return render_template('admin_historia.html', historia=hist, fotos=fotos)


@app.route('/admin/historia/foto/subir', methods=['POST'])
@login_required
def historia_foto_subir():
    nombre_imagen = guardar_imagen(request.files.get('imagen'))
    if nombre_imagen:
        foto = FotoGaleria(seccion='historia', imagen=nombre_imagen, descripcion=request.form.get('descripcion'))
        db.session.add(foto)
        db.session.commit()
    return redirect(url_for('admin_historia'))


@app.route('/admin/historia/foto/eliminar/<int:id>')
@login_required
def historia_foto_eliminar(id):
    foto = FotoGaleria.query.get_or_404(id)
    db.session.delete(foto)
    db.session.commit()
    return redirect(url_for('admin_historia'))


# ── Galería general ───────────────────────────────────────────────────────────

@app.route('/admin/galeria')
@login_required
def admin_galeria():
    fotos = FotoGaleria.query.filter_by(seccion='galeria').order_by(FotoGaleria.orden).all()
    return render_template('admin_galeria.html', fotos=fotos)


@app.route('/admin/galeria/subir', methods=['POST'])
@login_required
def galeria_foto_subir():
    nombre_imagen = guardar_imagen(request.files.get('imagen'))
    if nombre_imagen:
        foto = FotoGaleria(seccion='galeria', imagen=nombre_imagen, descripcion=request.form.get('descripcion'))
        db.session.add(foto)
        db.session.commit()
    return redirect(url_for('admin_galeria'))


@app.route('/admin/galeria/eliminar/<int:id>')
@login_required
def galeria_foto_eliminar(id):
    foto = FotoGaleria.query.get_or_404(id)
    db.session.delete(foto)
    db.session.commit()
    return redirect(url_for('admin_galeria'))


# ── Inicializar base de datos ─────────────────────────────────────────────────

with app.app_context():
    db.create_all()

    if not Admin.query.first():
        admin = Admin(
            username=os.environ.get('ADMIN_USERNAME'),
            password=generate_password_hash(os.environ.get('ADMIN_PASSWORD'))
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Usuario admin creado: {os.environ.get('ADMIN_USERNAME')}")


if __name__ == '__main__':
    app.run(debug=True)