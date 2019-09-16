#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import sys
from imp import reload

reload(sys)
#sys.setdefaultencoding('utf8')
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, IntegerField, StringField, TextAreaField, PasswordField, validators, DateField, DateTimeField
from passlib.hash import sha256_crypt
import logging
import os
import datetime
from functools import wraps

userID = 0

images = os.path.join('static', 'images')

app = Flask (__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'tennis_matcher'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = images
#init MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'tennis_ball.png')
    full_filename_plus = os.path.join(app.config['UPLOAD_FOLDER'], 'plus_icon_2.png')
    full_filename_list = os.path.join(app.config['UPLOAD_FOLDER'], 'list_icon_2.png')
    full_filename_profile = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_icon_2.png')
    return render_template('home.html', user_image = full_filename, plus_icon = full_filename_plus, list_icon = full_filename_list, profile_icon = full_filename_profile)
    
@app.route('/about')
def about():
    return render_template('about.html')


class RegisterForm(Form):
    id =IntegerField('Šifra korisnika', render_kw={'readonly': True})
    ime = StringField('Ime', [validators.Length(min=1, max=50)])
    prezime = StringField('Prezime', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    godiste = DateField(u'Godište', format = '%Y-%m-%d')
    telefon = StringField('Broj mobitela', [validators.Length (min=6, max=50)])
    password = PasswordField('Lozinka', [validators.EqualTo('confirm', message = 'Passwords do not match'), validators.Length(min=6, max=50)])
    confirm  = PasswordField('Potvrdi lozinku')
    pobjede = IntegerField('Broj pobjeda', render_kw={'readonly': True})
    porazi  = IntegerField('Broj poraza', render_kw={'readonly': True})
    mecevi  = IntegerField('Broj odigranih mečeva', render_kw={'readonly': True})

    @app.route('/register', methods= ['GET', 'POST'])
    def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
            ime = form.ime.data
            prezime = form.prezime.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))
            godiste = form.godiste.data
            telefon = form.telefon.data

            #Create cursor
            cur = mysql.connection.cursor()
            #execute query
            try:
                cur.execute("INSERT INTO igrac(email, ime, prezime, godiste, broj_telefona, password) VALUES(%s, %s, %s, %s, %s, %s)", (email, ime, prezime, godiste, telefon, password))
            except:
                 flash('Neuspješna Registracija. Već postoji korisnik s ovim emailom','danger')
                 return redirect(url_for('register'))
           
            #commit to DB
            mysql.connection.commit()
        
            #close db 
            cur.close()

            flash(u'Uspješno ste se registrirali. Možete se prijaviti', 'success')

            redirect(url_for('login'))
            return redirect(url_for('login'))
       
        return render_template('register.html', form=form)

        # User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM igrac WHERE email = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            global userID
            userID = data['id']
            session['ime'] = data['ime']
            session['prezime'] = data['prezime']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['id'] = userID
 
                flash(u'Uspješno ste se prijavili', 'success')
                return redirect(url_for('index'))
            else:
                error = u'Neuspješna prijava'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = u'Nije pronađen korisnik s ovim emailom'
            return render_template('login.html', error=error)
           

    return render_template('login.html')

    #check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash(u'Niste prijavljeni. Molimo prijavite se.', 'danger')
            return redirect(url_for('login'))
    return wrap

    # Logout
@app.route('/logout')
def logout():
    session.clear()
    flash(u'Uspješna odjava', 'success')
    return redirect(url_for('login'))

class MyProfile(Form):
    id =IntegerField('Šifra korisnika', render_kw={'readonly': True})
    ime = StringField('Ime', [validators.Length(min=1, max=50)])
    prezime = StringField('Prezime', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    godiste = DateField(u'Godište',  format = '%d-%m-%Y', render_kw={'readonly': True})
    telefon = StringField('Broj mobitela', [validators.Length (min=6, max=50)])
    pobjede = IntegerField('Broj pobjeda', render_kw={'readonly': True})
    porazi  = IntegerField('Broj poraza', render_kw={'readonly': True})
    mecevi  = IntegerField('Broj odigranih mečeva', render_kw={'readonly': True})

@app.route('/my_profile',methods= ['GET', 'POST'])
def my_profile():
    form = MyProfile(request.form)

    if request.method == 'POST' and form.validate:
            # Get Form Fields
        ime     = form.ime.data
        prezime = form.prezime.data
        email   = form.email.data
        godiste = form.godiste.data
        telefon = form.telefon.data
        try:
            cur = mysql.connection.cursor()
            update = cur.execute("UPDATE igrac SET ime = %s, prezime = %s, email = %s, godiste = %s, broj_telefona = %s WHERE id = %s",
            (ime, prezime, email, godiste, telefon, [session['id']]))
            flash('Uspješno spremljeno.', 'success')
            mysql.connection.commit()
            cur.close()
            
            return redirect (url_for('my_profile'))

        except Exception as e: 
             flash('Neuspješno', 'danger')
             return render_template('my_profile.html', form = form)

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM igrac WHERE id = %s", [session['id']])
    igrac = cur.fetchone()

    result_2 = cur.execute("SELECT pobjednik_id FROM mec where pobjednik_id = %s ", [session['id']])
    pobjede = cur.fetchall()
    broj_pobjeda = 0

    for pobjeda in pobjede:
        broj_pobjeda = broj_pobjeda + 1

    result_3 = cur.execute("SELECT gubitnik_id FROM mec WHERE gubitnik_id = %s", [session['id']])
    porazi = cur.fetchall()
    broj_poraza = 0
    
    for poraz in porazi:
        broj_poraza = broj_poraza +1

    resul_4 = cur.execute("SELECT * FROM mec WHERE gubitnik_id = %s or pobjednik_id = %s", [session['id'], session['id']])
    mecevi = cur.fetchall()
    broj_meceva = 0

    for mec in mecevi:
        broj_meceva = broj_meceva + 1

    #populate form fields
    form.ime.data      = igrac['ime']
    form.prezime.data  = igrac['prezime']
    form.email.data    = igrac['email']
    form.godiste.data  = igrac['godiste']
    form.telefon.data  = igrac['broj_telefona']
    form.id.data       = igrac['id']
    form.pobjede.data  = broj_pobjeda
    form.porazi.data   = broj_poraza
    form.mecevi.data   = broj_meceva

    cur.close()


    return render_template('my_profile.html', form = form)


class ChangePassword(Form):
    id =IntegerField('Šifra korisnika', render_kw={'readonly': True})
    ime = StringField('Ime', [validators.Length(min=1, max=50)])
    old_password = PasswordField('Stara lozinka', [validators.length (min = 6, max = 50)])
    new_password = PasswordField('Nova lozinka', [validators.EqualTo('confirm', message = 'Passwords do not match'), validators.Length(min=6, max=50)])
    confirm  = PasswordField('Potvrdi lozinku')
   
#change password 
@app.route('/change_password', methods = ['GET','POST'])
@is_logged_in
def change_password():
    form = ChangePassword(request.form)
    if request.method == 'POST':
        
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm      = request.form['confirm']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM igrac WHERE id = %s", [session['id']])

        data = cur.fetchone()
        password = data['password']
            
            
        if sha256_crypt.verify(old_password, password):
                
            if new_password == confirm:
                    password_to_set = sha256_crypt.encrypt(str(new_password))
                    password_to_compare = sha256_crypt.encrypt(str(confirm))                   
                    try:
                        update = cur.execute("UPDATE igrac SET password = %s where id = %s ", (password_to_set, [session['id']]))
                        mysql.connection.commit()
                        
                    except Exception as e:
                        print(e)
            else:
                    error = u'Lozinke se ne podudaraju'
                    return render_template('change_password.html', form = form, error=error)

            logout()
            flash('Uspješna promjena lozinke. Prijavite se s novom lozinkom', 'success')
            return render_template('login.html')

        else:
            error = u'Stara lozinka nije točna'
            return render_template('change_password.html', form = form, error=error)
            # Close connection
            cur.close()

    return render_template('change_password.html', form = form)


class PlayerProfile(Form):
    id =IntegerField('Šifra korisnika', render_kw={'readonly': True})
    ime = StringField('Ime',[validators.Length(min=1, max=50)], render_kw={'readonly': True} )
    prezime = StringField('Prezime', [validators.Length(min=1, max=50)], render_kw={'readonly': True})
    email = StringField('Email', [validators.Length(min=6, max=50)], render_kw={'readonly': True})
    godiste = DateField(u'Godište', format = '%d-%m-%Y', render_kw={'readonly': True})
    telefon = StringField('Broj mobitela', [validators.Length (min=6, max=50)],render_kw={'readonly': True})
    pobjede = IntegerField('Broj pobjeda', render_kw={'readonly': True})
    porazi  = IntegerField('Broj poraza', render_kw={'readonly': True})
    mecevi  = IntegerField('Broj odigranih mečeva', render_kw={'readonly': True})

#player profile
@app.route('/player_profile/<string:id>', methods = ['GET'])
@is_logged_in
def player_profile(id):

    form = PlayerProfile(request.form)

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM igrac WHERE id = %s", [id])
    igrac = cur.fetchone()

    result_2 = cur.execute("SELECT pobjednik_id FROM mec where pobjednik_id = %s ", [id])
    pobjede = cur.fetchall()
    broj_pobjeda = 0

    for pobjeda in pobjede:
        broj_pobjeda = broj_pobjeda + 1
        print ("broj pobjeda ", broj_pobjeda)

    result_3 = cur.execute("SELECT gubitnik_id FROM mec WHERE gubitnik_id = %s", [id])
    porazi = cur.fetchall()
    broj_poraza = 0
    
    for poraz in porazi:
        broj_poraza = broj_poraza +1

    resul_4 = cur.execute("SELECT * FROM mec WHERE gubitnik_id = %s or pobjednik_id = %s", [id, id])
    mecevi = cur.fetchall()
    broj_meceva = 0

    for mec in mecevi:
        broj_meceva = broj_meceva + 1

    #populate form fields
    form.ime.data      = igrac['ime']
    form.prezime.data  = igrac['prezime']
    form.email.data    = igrac['email']
    form.godiste.data  = igrac['godiste']
    form.telefon.data  = igrac['broj_telefona']
    form.id.data       = igrac['id']
    form.pobjede.data  = broj_pobjeda
    form.porazi.data   = broj_poraza
    form.mecevi.data   = broj_meceva

    cur.close()


    return render_template('player_profile.html', form = form, ime = igrac['ime'], prezime = igrac['prezime'])


 #my_matches
@app.route('/my_matches')
@is_logged_in
def my_matches():
    #create cursor
    
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM mec WHERE igrac1_id = %s OR igrac2_id =%s",([session['id']], [session['id']]))

    mecevi = cur.fetchall()
    if result>0:
        second_fetch = cur.execute("SELECT * FROM igrac where id = %s", [session['id']])
        igraci = cur.fetchall()
        return render_template('my_matches.html', mecevi=mecevi, igraci = igraci)
    else:
        msg = 'Nemate odigranih ili kreiranih mečeva.'
        return render_template('my_matches.html', msg=msg)
    #close connection
    cur.close()
    
    
    return render_template('my_matches.html', mec=mecevi)

    
class JoinMecForm(Form):
        mec_id  = IntegerField('Šifra korisnika', render_kw={'readonly': True})
        prvi_igrac = StringField('Domaćin', render_kw={'readonly': True})
        prvi_igracID = IntegerField('Šifra prvog igrača', render_kw={'readonly': True})
        drugi_igrac = StringField('Gost', render_kw={'readonly': True})
        drugi_igracID = IntegerField('Šifra drugog igrača', render_kw={'readonly': True})
        igrac1_set1 = IntegerField('Prvi set', [validators.required()])
        igrac1_set2 = IntegerField('Drugi set',[validators.required()])
        igrac1_set3 = IntegerField('Treći set', [validators.required()])
        igrac2_set1 = IntegerField('Prvi set', [validators.required()])
        igrac2_set2 = IntegerField('Drugi set', [validators.required()])
        igrac2_set3 = IntegerField('Treći set', [validators.required()])
        pobjednikID = IntegerField('Šifra pobjednika', render_kw={'readonly': True})
        gubitnikID  = IntegerField('Šifra gubitnika', render_kw={'readonly': True})
        otvoren     = IntegerField('Status meča', render_kw={'readonly': True})
        lokacija    = StringField('Lokacija', render_kw={'readonly': True})
        vrijeme     = DateTimeField('Vrijeme odigravanja', render_kw={'readonly': True})

@app.route('/join_match/<string:id>', methods = ['GET', 'POST'])
@is_logged_in
def join_match(id):
    form = JoinMecForm(request.form)
    cur = mysql.connection.cursor()

    #čim otvori ovu stranicu stavi igrac2_id kao gostujući igrac i da je mec dogovoren
    query = cur.execute("UPDATE mec SET igrac2_id = %s, otvoren = '0' WHERE id = %s", ([session['id']], [id]))
    mysql.connection.commit()

    result2 = cur.execute("SELECT * FROM igrac")
    igraci = cur.fetchall()

    result = cur.execute("SELECT * FROM mec WHERE id = %s", [id])
    mec = cur.fetchone()

    for igrac in igraci:
        if(igrac['id'] == mec['igrac1_id']):
            domacin = igrac['ime'] + " " + igrac['prezime']
        if(igrac['id'] == mec['igrac2_id']):
            gost = igrac['ime'] + " " + igrac['prezime']

    

    #submit button...
    if request.method == 'POST' and form.validate():
        igrac1_set1 = form.igrac1_set1.data
        igrac1_set2 = form.igrac1_set2.data
        igrac1_set3 = form.igrac1_set3.data
        igrac2_set1 = form.igrac2_set1.data
        igrac2_set2 = form.igrac2_set2.data
        igrac2_set3 = form.igrac2_set3.data
        

        igrac1_bodovi = 0
        igrac2_bodovi = 0
        pobjednik_id = 0
        gubitnik_id = 0
        if(igrac1_set1 > igrac2_set1): igrac1_bodovi = igrac1_bodovi +1
        else: igrac2_bodovi = igrac2_bodovi + 1
        if(igrac1_set2 > igrac2_set2): igrac1_bodovi = igrac1_bodovi +1
        else: igrac2_bodovi = igrac2_bodovi + 1
        if(igrac1_set3 > igrac2_set3): igrac1_bodovi = igrac1_bodovi + 1
        else: igrac2_bodovi = igrac2_bodovi + 1
        
        if(igrac1_bodovi > igrac2_bodovi): 
            pobjednik_id = mec['igrac1_id']
            gubitnik_id = mec['igrac2_id']
        else: 
            pobjednik_id = mec['igrac2_id']
            gubitnik_id = mec['igrac1_id']


        update = cur.execute("UPDATE mec SET igrac1_set1 = %s, igrac1_set2 = %s, igrac1_set3 = %s, igrac2_set1 = %s, igrac2_set2 = %s, igrac2_set3 = %s, pobjednik_id = %s, gubitnik_id = %s WHERE id = %s", (igrac1_set1, igrac1_set2, igrac1_set3, igrac2_set1, igrac2_set2, igrac2_set3, pobjednik_id, gubitnik_id, id) )
        mysql.connection.commit()
        pobjednik = ""
        for igrac in igraci:
            if(igrac['id'] == pobjednik_id):
             pobjednik = igrac['ime'] + " " + igrac['prezime']
        
        flash('Čestitamo pobjedniku ' + pobjednik + ' na pobjedi!', 'success')


    termin = mec['vrijeme_odigravanja']
    termin = termin.strftime('%d-%m-%Y:%H:%m')
    termin = datetime.datetime.strptime(termin, '%d-%m-%Y:%H:%M')

    #populate form fields
    form.mec_id.data        = mec['id']
    form.prvi_igracID.data  = mec['igrac1_id']
    form.drugi_igracID.data = mec['igrac2_id']
    form.igrac1_set1.data   = mec['igrac1_set1']
    form.igrac1_set2.data   = mec['igrac1_set2']
    form.igrac1_set3.data   = mec['igrac1_set3']
    form.igrac2_set1.data   = mec['igrac2_set2']
    form.igrac2_set2.data   = mec['igrac2_set3']
    form.igrac2_set3.data   = mec['igrac2_set3']
    form.lokacija.data      = mec['lokacija']
    form.vrijeme.data       = termin

   

    form.prvi_igrac.data = domacin
    form.drugi_igrac.data = gost
   

    return render_template('join_match.html', form = form, termin = termin, prvi_igrac = domacin, drugi_igrac = gost)

   
@app.route('/create_new_match',methods=['GET', 'POST'])
@is_logged_in
def create_match():

    if request.method == 'POST':
        #Get Form Fields
        lokacija = request.form['lokacija']
        termin = request.form['termin']

        try:    
            d = datetime.datetime.strptime(termin, '%Y-%m-%dT%H:%M')
            new_date = d.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            flash('Polje za termin ne može biti prazno!', 'danger')
            return redirect(url_for('create_match'))

         #create cursor
        cur = mysql.connection.cursor()

        #execute
        try:
            cur.execute("INSERT INTO mec (igrac1_id, lokacija, vrijeme_odigravanja, otvoren) VALUES (%s,%s, %s, %s)", (session['id'], [lokacija], [new_date], '1'))
            
        except:
             flash('Neuspješno kreiranje. Pokušajte ponovno','danger')
             return redirect(url_for('create_match'))

        flash('Uspješno kreiran meč.', 'success')     
        mysql.connection.commit()

        #close connection
        cur.close()

        return redirect(url_for('my_matches'))

    return render_template('create_new_match.html')

@app.route ('/show_matches', methods=['GET'])
@is_logged_in
def show_matches():
    full_filename_reketi  = os.path.join(app.config['UPLOAD_FOLDER'], 'reketi.png')

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM mec WHERE otvoren = '1' and igrac1_id != %s and igrac2_id != %s", ([session['id']], [session['id']]))

    mecevi = cur.fetchall()
    
    if result>0:
        second_fetch = cur.execute("SELECT * FROM igrac")
        igraci = cur.fetchall()
        return render_template('show_matches.html', mecevi=mecevi, igraci = igraci, reketi_icon = full_filename_reketi)
    else:
        flash('Nije pronađen niti jedan meč.','danger')
        return redirect (url_for('index'))
    #close connection
    cur.close()

    return render_template('show_matches.html')

class MecForm(Form):

    mec_id        = IntegerField('Šifra korisnika', render_kw={'readonly': True})
    prvi_igrac    = StringField('Domaćin', render_kw={'readonly': True})
    prvi_igracID  = IntegerField('Šifra prvog igrača', render_kw={'readonly': True})
    drugi_igrac   = StringField('Gost', render_kw={'readonly': True})
    drugi_igracID = IntegerField('Šifra drugog igrača', render_kw={'readonly': True})
    igrac1_set1   = IntegerField('Prvi set', render_kw={'readonly': True})
    igrac1_set2   = IntegerField('Drugi set', render_kw={'readonly': True})
    igrac1_set3   = IntegerField('Treći set', render_kw={'readonly': True})
    igrac2_set1   = IntegerField('Prvi set', render_kw={'readonly': True})
    igrac2_set2   = IntegerField('Drugi set', render_kw={'readonly': True})
    igrac2_set3   = IntegerField('Treći set', render_kw={'readonly': True})
    pobjednikID   = IntegerField('Šifra pobjednika', render_kw={'readonly': True})
    gubitnikID    = IntegerField('Šifra gubitnika', render_kw={'readonly': True})
    otvoren       = IntegerField('Status meča', render_kw={'readonly': True})
    lokacija      = StringField('Lokacija', render_kw={'readonly': True})
    vrijeme       = DateTimeField('Vrijeme odigravanja', format='%d-%m-%Y %H:%M:%S', render_kw={'readonly': True})


@app.route('/match_details/<string:id>', methods = ['GET', 'POST'])
@is_logged_in
def match_details(id):

    form = MecForm(request.form)

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM mec WHERE id = %s", [id])
    mec = cur.fetchone()

    #populate form fields
    form.mec_id.data        = mec['id']
    form.prvi_igracID.data  = mec['igrac1_id']
    form.drugi_igracID.data = mec['igrac2_id']
    form.igrac1_set1.data   = mec['igrac1_set1']
    form.igrac1_set2.data   = mec['igrac1_set2']
    form.igrac1_set3.data   = mec['igrac1_set3']
    form.igrac2_set1.data   = mec['igrac2_set2']
    form.igrac2_set2.data   = mec['igrac2_set3']
    form.igrac2_set3.data   = mec['igrac2_set3']
    form.pobjednikID.data   = mec['pobjednik_id']
    form.gubitnikID.data    = mec['gubitnik_id']
    form.otvoren.data       = mec['otvoren']
    form.lokacija.data      = mec['lokacija']
    form.vrijeme.data       = mec['vrijeme_odigravanja']

    domacin = ""
    gost = ""

    result2 = cur.execute("SELECT * FROM igrac")
    igraci = cur.fetchall()

    for igrac in igraci:
        if(igrac['id'] == mec['igrac1_id']):
            domacin = igrac['ime'] + " " + igrac['prezime']
        if(igrac['id'] == mec['igrac2_id']):
            gost = igrac['ime'] + " " + igrac['prezime']

    form.prvi_igrac.data = domacin
    form.drugi_igrac.data = gost

    cur.close()
    
    return render_template('match_details.html', form=form)
        
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug = True)
    
