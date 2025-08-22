import os
from pymongo import MongoClient
import secrets
from flask import Flask, render_template, request, redirect, flash, jsonify, url_for, session
from bson import ObjectId
import hashlib
from flask_mail import Mail, Message
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from os.path import join, dirname 

# Load environment variables from .env files
load_dotenv()
dotenv_path = join(dirname(__file__), '.env')

app = Flask(__name__)

# Set secret key for Flask app
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(24))

# MongoDB connection string and database name
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://test:sparta@cluster0.voyyor4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "dbPortofolio")

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db.dbPortfolio

# Email configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'backupeja30@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'kolypckhxkkqdioz')


def time2str(date):
    """Converts a date to a human-readable relative time format."""
    now = datetime.now()
    time_diff = now - date

    if time_diff.total_seconds() < 60:
        return f"{int(time_diff.total_seconds())} seconds ago"
    elif time_diff.total_seconds() < 3600:
        return f"{int(time_diff.total_seconds() / 60)} minutes ago"
    elif time_diff.total_seconds() < 86400:
        return f"{int(time_diff.total_seconds() / 3600)} hours ago"
    else:
        return date.strftime("%Y-%m-%d %H:%M")

# Initialize Flask-Mail
mail = Mail(app)

# Check admin decorator


@app.route('/profile')
def profile():
    username = session['username']
    user = db.user.find_one({"username": username})
    if user:
        profile_name = user.get('profile_name', 'Guest')
        return render_template('profile.html', username=username, profile_name=profile_name)
    else:
        flash('User not found', 'error')
        return redirect(url_for('index'))

# New route for editing profile
@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    username = session['username']
    user = db.user.find_one({"username": username})
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_profile_name = request.form.get('profile_name')
        
        # Validate and update the user data in the database
        if new_username and new_profile_name:
            update_result = db.user.update_one(
                {"username": username},
                {"$set": {"username": new_username, "profile_name": new_profile_name}}
            )
            
            if update_result.modified_count > 0:
                flash('Profile updated successfully', 'success')
                # Update session username if it has changed
                session['username'] = new_username
                return redirect(url_for('profile'))
            else:
                flash('Failed to update profile', 'error')
        
    return render_template('edit_profile.html', username=username, profile_name=user.get('profile_name', 'Guest'))
# Route for the homepage
@app.route('/')
def index():
    # Fetch and process berita data
    berita_data = list(db.berita.find({}))
    for berita_item in berita_data:
        berita_item['time_str'] = time2str(berita_item['time'])
    
    # Fetch and process experience data
    experience_data = list(db.experience.find({}))
    for experience_item in experience_data:
        experience_item['time_str'] = time2str(experience_item['time'])
    
    portfolio_data = list(db.portfolio.find({}))
    for portfolio_item in portfolio_data:
        portfolio_item['time_str'] = time2str(portfolio_item['time'])    
    # Render the template with both sets of data
    return render_template('index.html', berita=berita_data, experience=experience_data, portfolio=portfolio_data)


@app.route('/index')
def home():
    berita_data = list(db.berita.find({}))
    for berita_item in berita_data:
        berita_item['time_str'] = time2str(berita_item['time'])
    return render_template('index.html', berita=berita_data)

@app.route('/berita', methods=['GET'])
def berita():
    berita_data = list(db.berita.find({}))
    for berita_item in berita_data:
        berita_item['time_str'] = time2str(berita_item['time'])
    return render_template('berita.html', berita=berita_data)

@app.route('/addBerita', methods=['GET', 'POST'])
def addberita():
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        gambar = request.files['gambar']
        
        if gambar:
            namaGambarAsli = gambar.filename
            namafileGambar = namaGambarAsli.split('/')[-1]
            file_path = f'static/imgGambar/{namafileGambar}'
            gambar.save(file_path)
        else:
            namafileGambar = None
            
        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
            'gambar': namafileGambar,
            'time': datetime.now()  # Tambahkan waktu saat ini
        }
        
        db.berita.insert_one(doc)
        return redirect(url_for("berita"))
    
    return render_template('AddBerita.html')

@app.route('/editBerita/<string:_id>', methods=['GET', 'POST'])
def editberita(_id):
    if request.method == 'POST':
        form_id = request.form['_id']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        uploaded_gambar = request.files['gambar']
        
        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
        }
        
        if uploaded_gambar:
            try:
                namaGambarAsli = uploaded_gambar.filename
                namafileGambar = namaGambarAsli.split('/')[-1]
                file_path = f'static/imgGambar/{namafileGambar}'
                
                # Pastikan direktori tempat menyimpan file ada
                if not os.path.exists('static/imgGambar'):
                    os.makedirs('static/imgGambar')
                
                uploaded_gambar.save(file_path)
                doc['gambar'] = namafileGambar
            except Exception as e:
                return f"Error saving file: {str(e)}", 500  # Tanggapi jika terjadi kesalahan saat menyimpan file
        
        try:
            db.berita.update_one({"_id": ObjectId(form_id)}, {"$set": doc})
            return redirect(url_for("berita"))
        except Exception as e:
            return f"Error updating database: {str(e)}", 500  # Tanggapi jika terjadi kesalahan saat memperbarui basis data
    
    # Ambil data dari MongoDB berdasarkan _id
    data = db.berita.find_one({"_id": ObjectId(_id)})
    if not data:
        return "Data not found", 404  # Tanggapi jika data tidak ditemukan
    
    return render_template('Editberita.html', data=data)


@app.route('/delete/<string:_id>', methods=['GET'])
def delete(_id):
    db.berita.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("berita"))



@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/service')
def service():
    return render_template("service.html")

@app.route('/certification')
def certification():
    sertifikat_data = list(db.sertifikat.find({}))  # Mengambil data sertifikat dari database
    for sertifikat_item in sertifikat_data:
        sertifikat_item['time_str'] = time2str(sertifikat_item['time'])  # Mengubah waktu menjadi string format
    
    # Debugging output
    print("Data fetched from database: ", sertifikat_data)
    
    return render_template('certification.html', sertifikat=sertifikat_data)  # Ensure template name is correct

@app.route('/sertifikat', methods=['GET'])
def sertifikat():
    sertifikat_data = list(db.sertifikat.find({}))
    for sertifikat_item in sertifikat_data:
        sertifikat_item['time_str'] = time2str(sertifikat_item['time'])
    return render_template('sertifikat.html', sertifikat=sertifikat_data)

@app.route('/addSertifikat', methods=['GET', 'POST'])
def addsertifikat():
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        gambar = request.files['gambar']
        link = request.form['link']
        
        if not link.startswith('http://') and not link.startswith('https://'):
            link = 'http://' + link

        # Ensure the directory exists
        os.makedirs('static/imgSertifikat', exist_ok=True)

        if gambar:
            namaGambarAsli = gambar.filename
            namafileGambar = os.path.basename(namaGambarAsli)  # Use os.path.basename to handle file name
            file_path = os.path.join('static', 'imgSertifikat', namafileGambar)  # Use os.path.join for the file path

            try:
                gambar.save(file_path)
            except Exception as e:
                # Handle the exception (you can log it or print it)
                print(f"Failed to save file: {e}")
                return "File upload failed", 500
        else:
            namafileGambar = None

        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
            'gambar': namafileGambar,
            'link': link,
            'time': datetime.now()  # Add current time
        }

        # Assuming db is already defined and connected
        db.sertifikat.insert_one(doc)
        return redirect(url_for("sertifikat"))

    return render_template('AddSertifikat.html')
@app.route('/editSertifikat/<string:_id>', methods=['GET', 'POST'])
def editsertifikat(_id):
    if request.method == 'POST':
        form_id = request.form['_id']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        uploaded_gambar = request.files['gambar']
        link = request.form['link']
        
        if not link.startswith('http://') and not link.startswith('https://'):
            link = 'http://' + link

        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
            'link': link,
        }
        
        if uploaded_gambar:
            try:
                namaGambarAsli = uploaded_gambar.filename
                namafileGambar = namaGambarAsli.split('/')[-1]
                file_path = f'static/imgSertifikat/{namafileGambar}'
                
                # Ensure the directory exists
                if not os.path.exists('static/imgSertifikat'):
                    os.makedirs('static/imgSertifikat')
                
                uploaded_gambar.save(file_path)
                doc['gambar'] = namafileGambar
            except Exception as e:
                return f"Error saving file: {str(e)}", 500  # Handle file save error
        
        try:
            db.sertifikat.update_one({"_id": ObjectId(form_id)}, {"$set": doc})
            return redirect(url_for("sertifikat"))
        except Exception as e:
            return f"Error updating database: {str(e)}", 500  # Handle database update error
    
    data = db.sertifikat.find_one({"_id": ObjectId(_id)})
    if not data:
        return "Data not found", 404  # Handle data not found error
    
    return render_template('Editsertifikat.html', data=data)



@app.route('/deleteSertifikat/<string:_id>', methods=['GET'])
def delete_sertifikat(_id):
    db.sertifikat.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("sertifikat"))

@app.route('/certificate_detail/<certificate_id>')
def certificate_detail(certificate_id):
    certificate = db.sertifikat.find_one({"_id": ObjectId(certificate_id)})
    if not certificate:
        return "Certificate not found", 404
    return render_template('certificate_detail.html', certificate=certificate)

#EXPERINCE
@app.route('/pengalaman', methods=['GET'])
def pengalaman():
    experience_data = list(db.experience.find({}))
    for experience_item in experience_data:
        experience_item['time_str'] = time2str(experience_item['time'])
    return render_template('pengalaman.html', experience=experience_data)

@app.route('/experience', methods=['GET'])
def experience():
    experience_data = list(db.experience.find({}))
    for experience_item in experience_data:
        experience_item['time_str'] = time2str(experience_item['time'])
    return render_template('experience.html', experience=experience_data)

@app.route('/addExperience', methods=['GET', 'POST'])
def add_experience():
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        gambar = request.files['gambar']

        # Ensure the directory exists
        os.makedirs('static/imgExperience', exist_ok=True)

        if gambar:
            namaGambarAsli = gambar.filename
            namafileGambar = os.path.basename(namaGambarAsli)  # Use os.path.basename to handle file name
            file_path = os.path.join('static', 'imgExperience', namafileGambar)  # Use os.path.join for the file path

            try:
                gambar.save(file_path)
            except Exception as e:
                # Handle the exception (you can log it or print it)
                print(f"Failed to save file: {e}")
                return "File upload failed", 500
        else:
            namafileGambar = None

        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
            'gambar': namafileGambar,
            'time': datetime.now()  # Add current time
        }

        # Assuming db is already defined and connected
        db.experience.insert_one(doc)
        return redirect(url_for("experience"))

    return render_template('addExperience.html')

@app.route('/editExperience/<string:_id>', methods=['GET', 'POST'])
def edit_experience(_id):
    if request.method == 'POST':
        form_id = request.form['_id']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        uploaded_gambar = request.files['gambar']
        
        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
        }
        
        if uploaded_gambar:
            try:
                namaGambarAsli = uploaded_gambar.filename
                namafileGambar = namaGambarAsli.split('/')[-1]
                file_path = f'static/imgExperience/{namafileGambar}'
                
                # Pastikan direktori tempat menyimpan file ada
                if not os.path.exists('static/imgExperience'):
                    os.makedirs('static/imgExperience')
                
                uploaded_gambar.save(file_path)
                doc['gambar'] = namafileGambar
            except Exception as e:
                return f"Error saving file: {str(e)}", 500  # Tanggapi jika terjadi kesalahan saat menyimpan file
        
        try:
            db.experience.update_one({"_id": ObjectId(form_id)}, {"$set": doc})
            return redirect(url_for("experience"))
        except Exception as e:
            return f"Error updating database: {str(e)}", 500  # Tanggapi jika terjadi kesalahan saat memperbarui basis data
    
    # Ambil data dari MongoDB berdasarkan _id
    data = db.experience.find_one({"_id": ObjectId(_id)})
    if not data:
        return "Data not found", 404  # Tanggapi jika data tidak ditemukan
    
    return render_template('editExperience.html', data=data)

@app.route('/deleteExperience/<string:_id>', methods=['GET'])
def delete_experience(_id):
    db.experience.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("experience"))

@app.route('/experience_detail/<experience_id>')
def experience_detail(experience_id):
    experience = db.experience.find_one({"_id": ObjectId(experience_id)})
    if not experience:
        return "Experience not found", 404
    return render_template('experience_detail.html', experience=experience)



@app.route('/porto', methods=['GET'])
def porto():
    portfolio_data = list(db.portfolio.find({}))
    for portfolio_item in portfolio_data:
        portfolio_item['time_str'] = time2str(portfolio_item['time'])
    return render_template('porto.html', portfolio=portfolio_data)

@app.route('/portfolio', methods=['GET'])
def portfolio():
    portfolio_data = list(db.portfolio.find({}))
    for portfolio_item in portfolio_data:
        portfolio_item['time_str'] = time2str(portfolio_item['time'])
    return render_template('portofolio.html', portfolio=portfolio_data)

@app.route('/addPortfolio', methods=['GET', 'POST'])
def add_portfolio():
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        gambar = request.files['gambar']
        link = request.form['link']
        
        if not link.startswith('http://') and not link.startswith('https://'):
                link = 'http://' + link       
        # Ensure the directory exists
        os.makedirs('static/imgPortfolio', exist_ok=True)

        if gambar:
            namaGambarAsli = gambar.filename
            namafileGambar = os.path.basename(namaGambarAsli)
            file_path = os.path.join('static', 'imgPortfolio', namafileGambar)

            try:
                gambar.save(file_path)
            except Exception as e:
                print(f"Failed to save file: {e}")
                return "File upload failed", 500
        else:
            namafileGambar = None

        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
            'gambar': namafileGambar,
            'link': link,
            'time': datetime.now()
        }

        db.portfolio.insert_one(doc)
        return redirect(url_for("portfolio"))

    return render_template('AddPortofolio.html')

@app.route('/editPortfolio/<string:_id>', methods=['GET', 'POST'])
def edit_portfolio(_id):
    if request.method == 'POST':
        form_id = request.form['_id']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        uploaded_gambar = request.files['gambar']
        link = request.form['link']
        
        if not link.startswith('http://') and not link.startswith('https://'):
            link = 'http://' + link

        doc = {
            'nama': nama,
            'deskripsi': deskripsi,
            'link': link,
        }
        if uploaded_gambar:
            try:
                namaGambarAsli = uploaded_gambar.filename
                namafileGambar = namaGambarAsli.split('/')[-1]
                file_path = f'static/imgPortfolio/{namafileGambar}'
                
                if not os.path.exists('static/imgPortfolio'):
                    os.makedirs('static/imgPortfolio')
                
                uploaded_gambar.save(file_path)
                doc['gambar'] = namafileGambar
            except Exception as e:
                return f"Error saving file: {str(e)}", 500
        
        try:
            db.portfolio.update_one({"_id": ObjectId(form_id)}, {"$set": doc})
            return redirect(url_for("portfolio"))
        except Exception as e:
            return f"Error updating database: {str(e)}", 500
    
    data = db.portfolio.find_one({"_id": ObjectId(_id)})
    if not data:
        return "Data not found", 404
    
    return render_template('editPortofolio.html', data=data)

@app.route('/deletePortfolio/<string:_id>', methods=['GET'])
def delete_portfolio(_id):
    db.portfolio.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("portfolio"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Example login validation
        user = db.user.find_one({"username": username})
        if user and user['password'] == hashlib.sha256(password.encode('utf-8')).hexdigest():
            session['username'] = username
            return jsonify({"result": "success", "role": user['role']})
        else:
            return jsonify({"result": "fail", "msg": "Username or password is incorrect"})
    else:
        return render_template('login.html')


@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    
    result = db.user.find_one({
        "username": username_receive,
        "password": pw_hash,
    })
    
    if result:
        session['username'] = username_receive
        return jsonify({"result": "success"})
    else:
        return jsonify({"result": "fail", "msg": "Username or password is incorrect"})

# Route for the logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Route for the appointment page
@app.route('/appointment')
def appointment():
    return render_template('appointment.html')

# Route for handling user registration (sign up)
@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    role_receive = request.form['role_give']
    
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
        "profile_name": username_receive,
        "profile_info": "",
        "role": role_receive
    }
    
    db.user.insert_one(doc)
    return jsonify({'result': 'success'})

# Endpoint to check for duplicate username during registration
@app.route("/sign_up/check_dup", methods=["POST"])
def check_dup():
    username_receive = request.form["username_give"]
    
    # Check if the username already exists in the database
    existing_user = db.user.find_one({"username": username_receive})
    
    if existing_user:
        return jsonify({"exists": True, "msg": "Username sudah digunakan."})
    else:
        return jsonify({"exists": False, "msg": "Username tersedia untuk digunakan!"})

# Route for the admin dashboard
@app.route('/admin')
def admin():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/schedule_appointment', methods=['POST'])
def schedule_appointment():
    # Retrieve form data
    nama = request.form['nama']
    phone = request.form['phone']
    consultation_type = request.form['consultation_type']
    discussion_topic = request.form['discussion_topic']
    date = request.form['date']
    time = request.form['time']
    
    # Create a document to insert into MongoDB
    konsultasi = {
        'nama': nama,
        'phone': phone,
        'consultation_type': consultation_type,
        'discussion_topic': discussion_topic,
        'date': date,
        'time': time,
        'timestamp': datetime.now()
    }
    
    # Insert the document into the 'konsultasi' collection
    db.konsultasi.insert_one(konsultasi)
    
    # Flash a success message
    flash('Jadwal konsultasi berhasil dikirim!', 'success')
    
    # Prepare the appointment details to be rendered on the same page
    appointment = {
        'nama': nama,
        'phone': phone,
        'consultation_type': consultation_type,
        'discussion_topic': discussion_topic,
        'date': date,
        'time': time
    }
    
    # Render the appointment page with appointment details
    return render_template('appointment.html', appointment=appointment)

@app.route('/consultations', methods=['GET'])
def consultations():
    consultations_data = list(db.konsultasi.find({}))
    for consultation in consultations_data:
        consultation['time_str'] = time2str(consultation['timestamp'])
    return render_template('jadwal_konsultasi.html', consultations=consultations_data)

@app.route('/delete_consultation/<consultation_id>', methods=['POST'])
def delete_consultation(consultation_id):
    db.konsultasi.delete_one({'_id': ObjectId(consultation_id)})
    flash('Consultation schedule deleted successfully!', 'success')
    return redirect('/consultations')

@app.route('/article_detail/<article_id>')
def article_detail(article_id):
    article = db.berita.find_one({"_id": ObjectId(article_id)})
    if not article:
        return "Article not found", 404
    return render_template('article_detail.html', article=article)




@app.route('/portfolio_detail/<portfolio_id>')
def portfolio_detail(portfolio_id):
    portfolio_item = db.portfolio.find_one({"_id": ObjectId(portfolio_id)})
    if not portfolio_item:
        return "Portfolio item not found", 404
    return render_template('portofolio_detail.html', portfolio=portfolio_item)


@app.route('/pages')
def pages():
    berita_data = list(db.berita.find({}))
    for berita_item in berita_data:
        berita_item['time_str'] = time2str(berita_item['time'])
    return render_template('pojokbaca.html', berita=berita_data)

@app.route('/messages', methods=['GET'])
def messages():
    messages_data = list(db.messages.find({}))
    for message in messages_data:
        message['time_str'] = time2str(message['time'])
    return render_template('message.html', messages=messages_data)

# Endpoint to handle sending email from contact form
@app.route('/send_email', methods=['POST'])
def send_email():
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']
    
    doc = {
        'name': name,
        'email': email,
        'subject': subject,
        'message': message,
        'time': datetime.now()
    }
    db.messages.insert_one(doc)

    msg = Message(subject=subject, sender=email, recipients=['muhammadibnusetiawan1718@gmail.com'])
    msg.body = f'Name: {name}\nEmail: {email}\n\n{message}'

    try:
        mail.send(msg)
        flash('Email berhasil dikirim!', 'success')
    except Exception as e:
        flash('Terjadi kesalahan saat mengirim email: ' + str(e), 'danger')

    return redirect('/contact')

@app.route('/recent-articles', methods=['GET'])
def recent_articles():
    berita_data = list(db.berita.find({}))
    sorted_berita_data = sorted(berita_data, key=lambda x: x['time'], reverse=True)
    for berita_item in sorted_berita_data:
        berita_item['time_str'] = time2str(berita_item['time'])
    
    return render_template('pojokbaca.html', berita=sorted_berita_data)

@app.route('/recent-experiences', methods=['GET'])
def recent_experiences():
    experience_data = list(db.experiences.find({}))
    sorted_experience_data = sorted(experience_data, key=lambda x: x['time'], reverse=True)
    for experience_item in sorted_experience_data:
        experience_item['time_str'] = time2str(experience_item['time'])
    
    return render_template('experience.html', experiences=sorted_experience_data)


@app.route('/recent-portfolio', methods=['GET'])
def recent_portfolio():
    portfolio_data = list(db.portfolio.find({}))
    sorted_portfolio_data = sorted(portfolio_data, key=lambda x: x['time'], reverse=True)
    for portfolio_item in sorted_portfolio_data:
        portfolio_item['time_str'] = time2str(portfolio_item['time'])
    
    return render_template('porto.html', portfolio=sorted_portfolio_data)


@app.route('/recent-certificates', methods=['GET'])
def recent_certificates():
    sertifikat_data = list(db.sertifikat.find({}))
    sorted_sertifikat_data = sorted(sertifikat_data, key=lambda x: x['time'], reverse=True)
    for sertifikat_item in sorted_sertifikat_data:
        sertifikat_item['time_str'] = time2str(sertifikat_item['time'])
    
    return render_template('certification.html', sertifikat=sorted_sertifikat_data)
# Route for the contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Main entry point of the application
if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
