import backend_main
from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = "super secret key"
preference_id = 0
recommendation_table = None

# assigns unique preference id to user
def increment_preference():
    global preference_id
    with open('preference_id', 'r') as preference_file:
        preference_id = int(preference_file.read())

    preference_id += 1
    with open('preference_id', 'w') as preference_file:
        preference_file.write(str(preference_id))

# main page
@app.route("/", methods=['GET', 'POST'])
def main():
    return render_template('homepage.html')

# application icon
@app.route("/favicon.ico", methods=['GET'])
def get_image():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

# CREATE new user page
@app.route("/insert", methods=['GET', 'POST'])
def insert():
    return render_template('insert.html')

# UPDATE user preference
@app.route("/preference", methods=['GET', 'POST'])
def preference():
    if request.method == 'POST':
        netid = request.form.get("netid")
        if backend_main.check_entry(netid):
            gpa_weight = request.form.get("gpa_weight")
            professor_weight = request.form.get("professor_weight")
            credits_weight = request.form.get("credits_weight")
            backend_main.update_preferences(gpa_weight, professor_weight, credits_weight, netid)
            flash("Preferences successfully updated.")

            list_weights = {}
            list_weights['p.Rating'] = professor_weight
            list_weights['c.AvgGPA'] = gpa_weight
            list_weights['c.Credits'] = credits_weight
            rank_one = ''
            rank_two = ''
            rank_three = ''
            rank_four = ''
            for key, weight in list_weights.items():
                if weight == '1':
                    rank_one = key
                elif weight == '2':
                    rank_two = key
                elif weight == '3':
                    rank_three = key
                else:
                    rank_four = key
            df = backend_main.return_query(netid, rank_one, rank_two, rank_three, rank_four)
            increment_preference()
            return render_template('recommendations.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)
        else:
            flash("You are not in our system. Please enter as a new user.")
            return redirect(url_for('preference'))
    else:
        return render_template('preference.html')

# DELETE user 
@app.route("/delete", methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        netid = request.form.get("netid")
        if backend_main.check_entry(netid):
            backend_main.delete_user(netid)
            flash("User successfully deleted.")
            return render_template('homepage.html')
        else:
            flash("You do not exist in our system. Please return to homepage and enter as a new user.")
            return redirect(url_for('delete'))
    else:
        return render_template('delete.html')

# READ course recommendations for user
@app.route("/recommendations", methods=['POST', 'GET'])
def get_courses():
    global recommendation_table
    netid = request.form.get("netid")
    # if backend_main.check_entry(netid):
        # flash("You are already in our system. Please select another option.")
        # return redirect(url_for('main'))
    # else:
    name = request.form.get("name")
    year = request.form.get("year")
    credithours = request.form.get("credithours")
    majorname = request.form.get("major")
    try:
        backend_main.enter_user(netid, name, year, credithours, preference_id, majorname)
    except:
        flash("You are already in our system. Please select another option.")
        return redirect(url_for('main'))
    classes_taken = request.form.get("classes_taken")
    courses = backend_main.get_courses(classes_taken)
    for subject, number in courses.items():
        backend_main.enter_enrollments(netid, subject, number)

    list_weights = {}
    list_weights['p.Rating'] = request.form.get("professor_weight")
    list_weights['c.AvgGPA'] = request.form.get("gpa_weight")
    list_weights['c.Credits'] = request.form.get("credits_weight")
    backend_main.enter_preferences(preference_id, int(list_weights['c.AvgGPA']), int(list_weights['p.Rating']), int(list_weights['c.Credits']), netid)

    rank_one = ''
    rank_two = ''
    rank_three = ''
    rank_four = ''
    for key, weight in list_weights.items():
        if weight == '1':
            rank_one = key
        elif weight == '2':
            rank_two = key
        elif weight == '3':
            rank_three = key
        else:
            rank_four = key
    df = backend_main.return_query(netid, rank_one, rank_two, rank_three, rank_four)
    recommendation_table = df
    increment_preference()
    return render_template('recommendations.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)

@app.route("/recommendation_query", methods=['POST'])
def recommendation_query():
    subject = request.form.get("subject_query")
    new_df = backend_main.recommendation_query(recommendation_table, subject)
    return render_template('recommendations.html',  tables=[new_df.to_html(classes='data')], titles=new_df.columns.values)

@app.route("/user-prefs", methods=['GET', 'POST'])
def get_user_prefs():
    if request.method == 'POST':
        netid = request.form.get("netid")
        if backend_main.check_entry(netid):
            df = backend_main.get_user_data(netid)
            return render_template('user_preferences.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)
        else:
            flash("You are not in our system. Please return to the homepage to enter as a new user.")
            return redirect(url_for('get_user_prefs'))
    else:
        return render_template('user.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

