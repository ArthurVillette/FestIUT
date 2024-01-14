import base64
from PIL import Image
from app import app
from flask import render_template, request, redirect, url_for, make_response, send_file, jsonify, Response
from flask_login import login_required, login_user, logout_user, current_user
from io import BytesIO
from functools import wraps
from werkzeug.utils import secure_filename
from app.requests import *
from app.forms import *
from app import login_manager
from app.models import *
import datetime

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user = get_user_by_email(form.mail.data)
    if form.validate_on_submit():
        if user:
            if user.mdp_spectateur == form.mdp.data:
                login_user(user, force=True)
                return redirect(url_for('home'))
    return render_template('connexion.html', form=form)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if request.form.get("rechercheGroupe") != None:
            return redirect(url_for('rechercheGroupe', nomGroupe=request.form.get("rechercheGroupe")))
        selected_date_debut = request.form.get('dateDebut')
        selected_date_fin = request.form.get('dateFin')
        selected_place = request.form.get('place')
        filtered_concerts = filter_concerts(selected_date_debut,selected_date_fin, selected_place)
    else:
        date = datetime.datetime.now()
        selected_date_debut = date.today().strftime("%Y-%m-%d")
        selected_date_fin = (date + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        selected_place = '1'
        filtered_concerts = filter_concerts(selected_date_debut,selected_date_fin, selected_place)
    lieux = get_lieux()
    admin=False
    connecter=False
    if current_user.is_authenticated:
        connecter=True
        admin=current_user.is_admin()
    return render_template('accueil.html', 
                           concerts=filtered_concerts, 
                           selected_date_debut=selected_date_debut,
                           selected_date_fin=selected_date_fin, 
                           selected_place=selected_place,
                           connecter=connecter,
                           admin=admin,
                           lieux = lieux)

@app.route('/rechercheGroupe')
def rechercheGroupe():
    nomGroupe = request.args.get('nomGroupe')
    groupes = get_groupes_by_nom(nomGroupe)
    admin=False
    connecter=False
    if current_user.is_authenticated:
        connecter=True
        admin=current_user.is_admin()
    return render_template('rechercheGroupe.html', groupes=groupes,connecter=connecter,admin=admin)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/registration',methods=['GET','POST'])
def registration():
    form = RegistrationForm()
    form.validate_password(form.password)
    if form.validate_on_submit() and form.password.data == form.confirm_password.data:
        spectateur = Spectateur(nom_spectateur=form.username.data, email_spectateur=form.email.data, mdp_spectateur=form.password.data)
        print(spectateur)
        print(spectateur.nom_spectateur)
        print(spectateur.email_spectateur)
        print(spectateur.mdp_spectateur)
        db.session.add(spectateur)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('inscription.html', form=form)



@app.route("/groupes")
def groupes():
    """
        Cette fonction nous permet de nous diriger vers la page qui
        liste les parcours
    """
    admin=False
    connecter=False
    if current_user.is_authenticated:
        connecter=True
        admin=current_user.is_admin()
    liste_groupe = get_groupes()
    return render_template('groupes.html', liste_groupes = liste_groupe,connecter=connecter,admin=admin)

@app.route("/favoris")
def favoris():
    """
        Cette fonction nous permet de nous diriger vers la page qui
        liste les parcours
    """
    admin=False
    connecter=False
    liste_favoris = []
    if current_user.is_authenticated:
        connecter=True
        admin=current_user.is_admin()
        liste_favoris = get_favoris(current_user.get_id())
    
    print(current_user.get_id())
    print(liste_favoris)
    return render_template('favorie.html', liste_favoris = liste_favoris,connecter=connecter,admin=admin)


@app.route("/groupe/<int:id_groupe>")
def groupe_detail(id_groupe):
    groupes_semblable =[]
    admin=False
    connecter=False
    if current_user.is_authenticated:
        connecter=True
        admin=current_user.is_admin()
    groupe = get_groupes_by_id(id_groupe)
    groupe = groupe[0]
    
    style = get_style_by_id_groupe(groupe.id_groupe)
    style = style[0]
    print(style)
    artistes= get_artistes_by_id_groupe(groupe.id_groupe)
    like= est_favoris(id_groupe, current_user.get_id())
    groupes_semblable=get_groupe_by_style(style.id_style)  
    concerts=get_concert_by_id_groupe(id_groupe)
    instrument=[]
    for artiste in artistes:
        instrument.append(get_instrument_by_id_artiste(artiste.id_artiste))
   
    event = (get_event_by_id_groupe(groupe.id_groupe))
    concerts_et_lieux = [(concert, get_lieu_by_id(concert.id_lieu)) for concert in concerts]
    events_et_lieux = [(e, get_lieu_by_id(e.id_lieu)) for e in event]
    return render_template('groupe_info.html', groupe=groupe, style=style, connecter=connecter,admin=admin,artistes=artistes,like=like,groupes_semblable=groupes_semblable,concerts_et_lieux=concerts_et_lieux,instruments=instrument,events_et_lieux=events_et_lieux, image_groupe=image_groupe)

@app.route('/ajouter_aux_favoris/<int:id_groupe>', methods=['POST'])
def ajouter_aux_favoris(id_groupe):
    ajouter_favoris(id_groupe, current_user.get_id())
    return redirect(url_for('groupe_detail', id_groupe=id_groupe))

@app.route('/supprimer_des_favoris/<int:id_groupe>', methods=['POST'])
def supprimer_des_favoris(id_groupe):
    supprimer_favoris(id_groupe, current_user.get_id())
    return redirect(url_for('groupe_detail', id_groupe=id_groupe))
