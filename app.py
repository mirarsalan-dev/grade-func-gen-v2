from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import requests
from datetime import datetime
import config
from pdf_generator import generate_single_result_to_buffer, generate_batch_results_to_buffer
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_in_production')

@app.route('/')
def login_page():
    if 'username' in session:
        return redirect(url_for('route_user', username=session['username']))
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if username == "exam_cell" and password == "exam_admin":
        session['username'] = username
        session['user_type'] = "exam_cell"
        return redirect(url_for('route_user', username=username))

    if username == "principal_tcoe" and password == "tcoe":
        session['username'] = username
        session['user_type'] = "principal"
        return redirect(url_for('route_user', username=username))

    hod_req = requests.get(f"{config.FIREBASE_URL}/users/hod/{username}.json").json()
    if hod_req and hod_req.get('password') == password:
        session['username'] = username
        session['user_type'] = 'hod'
        session['branch'] = hod_req.get('branch')
        return redirect(url_for('route_user', username=username))

    fac_req = requests.get(f"{config.FIREBASE_URL}/users/faculty/{username}.json").json()
    if fac_req and fac_req.get('password') == password:
        if fac_req.get('status') == 'approved':
            session['username'] = username
            session['user_type'] = 'faculty'
            session['branch'] = fac_req.get('branch')
            return redirect(url_for('route_user', username=username))
        else:
            flash("Account pending approval from HOD.", "error")
            return redirect(url_for('login_page'))

    flash("Invalid Credentials", "error")
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard/<username>')
def route_user(username):
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('login_page'))

    user_type = session.get('user_type')
    if user_type == "principal": return redirect(url_for('principal_dashboard'))
    elif user_type == "hod": return redirect(url_for('hod_dashboard'))
    elif user_type == "exam_cell": return redirect(url_for('exam_cell_dashboard'))
    else: return redirect(url_for('teacher_portal'))

@app.route('/principal')
def principal_dashboard():
    if session.get('user_type') != "principal": return redirect(url_for('login_page'))
    return render_template('principal_dashboard.html', username=session['username'])

@app.route('/teacher')
def teacher_portal():
    if session.get('user_type') != "faculty": return redirect(url_for('login_page'))
    return render_template('teacher_portal.html', username=session['username'], branch=session.get('branch', 'IT'))

@app.route('/hod')
def hod_dashboard():
    if session.get('user_type') != "hod": return redirect(url_for('login_page'))
    return render_template('hod_dashboard.html', branch=session.get('branch', 'IT'), username=session['username'])

@app.route('/exam_cell')
def exam_cell_dashboard():
    if session.get('user_type') != "exam_cell": return redirect(url_for('login_page'))
    return render_template('exam_cell.html')

# --- STUDENT PORTAL ROUTES ---
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        branch = request.form.get('branch')
        semester = request.form.get('semester')
        gr_no = request.form.get('gr_no').strip().upper()
        dob = request.form.get('dob').strip() # Added Date of Birth extraction
        
        student_data = requests.get(f"{config.FIREBASE_URL}/students/{branch}/{semester}/{gr_no}.json").json()
        
        # Added DOB verification 
        if student_data and student_data.get('DOB') == dob:
            session['student_gr'] = gr_no
            session['student_branch'] = branch
            session['student_sem'] = semester
            session['student_name'] = student_data.get('Name')
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid GR Number or Date of Birth.", "error")
            
    return render_template('student_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_gr' not in session: return redirect(url_for('student_login'))
    return render_template('student_dashboard.html', gr=session['student_gr'], name=session['student_name'], branch=session['student_branch'], sem=session['student_sem'])

@app.route('/student_logout')
def student_logout():
    session.pop('student_gr', None)
    session.pop('student_branch', None)
    session.pop('student_sem', None)
    session.pop('student_name', None)
    return redirect(url_for('student_login'))

# --- USER MANAGEMENT API ROUTES ---
@app.route('/api/exam_cell/add_hod', methods=['POST'])
def api_add_hod():
    if session.get('user_type') != "exam_cell": return {"error": "Unauthorized"}, 401
    data = request.json
    payload = {"password": data['password'], "branch": data['branch']}
    if data.get('photo'): payload['photo'] = data['photo']
    requests.put(f"{config.FIREBASE_URL}/users/hod/{data['username']}.json", json=payload)
    return {"status": "success"}

@app.route('/api/exam_cell/add_faculty', methods=['POST'])
def api_add_faculty():
    if session.get('user_type') != "exam_cell": return {"error": "Unauthorized"}, 401
    data = request.json
    payload = {"password": data['password'], "branch": data['branch'], "status": "pending"}
    if data.get('photo'): payload['photo'] = data['photo']
    requests.put(f"{config.FIREBASE_URL}/users/faculty/{data['username']}.json", json=payload)
    return {"status": "success"}

@app.route('/api/exam_cell/edit_faculty/<username>', methods=['PATCH'])
def api_edit_faculty(username):
    if session.get('user_type') != "exam_cell": return {"error": "Unauthorized"}, 401
    data = request.json
    update_data = {}
    if data.get('password'): update_data['password'] = data['password']
    if data.get('photo'): update_data['photo'] = data['photo']
    if update_data: requests.patch(f"{config.FIREBASE_URL}/users/faculty/{username}.json", json=update_data)
    return {"status": "success"}

@app.route('/api/principal/edit_profile', methods=['PATCH'])
def api_edit_principal():
    if session.get('user_type') != "principal": return {"error": "Unauthorized"}, 401
    data = request.json
    update_data = {}
    if data.get('name'): update_data['name'] = data['name']
    if data.get('photo'): update_data['photo'] = data['photo']
    if update_data: requests.patch(f"{config.FIREBASE_URL}/users/principal/profile.json", json=update_data)
    return {"status": "success"}

@app.route('/api/exam_cell/remove_faculty/<username>', methods=['DELETE'])
def api_remove_faculty(username):
    if session.get('user_type') != "exam_cell": return {"error": "Unauthorized"}, 401
    requests.delete(f"{config.FIREBASE_URL}/users/faculty/{username}.json")
    return {"status": "success"}

@app.route('/api/hod/handle_approval', methods=['POST'])
def api_handle_approval():
    if session.get('user_type') != "hod": return {"error": "Unauthorized"}, 401
    data = request.json
    username = data['username']
    action = data['action']
    if action == 'approve': requests.patch(f"{config.FIREBASE_URL}/users/faculty/{username}.json", json={"status": "approved"})
    elif action == 'decline': requests.delete(f"{config.FIREBASE_URL}/users/faculty/{username}.json")
    return {"status": "success"}

# --- PDF & LOGGING API ROUTES ---
@app.route('/api/log_action', methods=['POST'])
def log_action():
    if 'username' not in session: return {"error": "Unauthorized"}, 401
    data = request.json
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": session['username'],
        "action": data.get("action", "UPDATE_MARKS"),
        "gr_no": data.get("gr_no"),
        "semester": data.get("semester"),
        "branch": session.get('branch', 'Unknown')
    }
    requests.post(f"{config.FIREBASE_URL}/logs.json", json=log_entry)
    return {"status": "success"}

@app.route('/download/single_result', methods=['POST'])
def download_single_result():
    data = request.json
    pdf_buffer = generate_single_result_to_buffer(
        name=data.get('name'), 
        gr_no=data.get('gr_no'), 
        branch=data.get('branch', session.get('branch', 'Information Technology')), 
        subjects=data.get('subjects')
    )
    filename = f"{data.get('gr_no')}_{data.get('name').replace(' ', '_')}_GradeCard.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/download/batch_results/<branch>/<semester>')
def download_batch_results(branch, semester):
    d = requests.get(f"{config.FIREBASE_URL}/students/{branch}/{semester}.json").json()
    if not d: return "No data found for this branch and semester", 404
    pdf_buffer = generate_batch_results_to_buffer(semester, d)
    return send_file(pdf_buffer, as_attachment=True, download_name=f"{branch}_{semester}_Master_Batch.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)