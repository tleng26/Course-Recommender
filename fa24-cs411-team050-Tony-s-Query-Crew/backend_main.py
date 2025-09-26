import pandas as pd
import os
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv
from mysql.connector import Error
# from sqlalchemy import create_engine

######################################### LOAD ENV #########################################
load_dotenv()

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
db_password = os.environ.get('CLOUD_SQL_DATABASE_PASSWORD')
connector = Connector()

def open_connection():
    conn = connector.connect(
    instance_connection_string=db_connection_name, 
    driver="pymysql", 
    password=db_password,                             
    user=db_user,                                
    db=db_name                                     
    )
    return conn

######################################### PARSE COURSES #########################################
def get_courses(classes_taken):
    prereqs = {}
    classes_all = classes_taken.split(', ')
    for c in classes_all:
        subject, number = c.split(' ')
        prereqs[subject] = number
    return prereqs

####################################### CHECK USER EXISTS #######################################
def check_entry(netid):
    con = open_connection()
    cursor = con.cursor()
    cursor.execute(f"""SELECT COUNT(*) FROM User WHERE NetID = "{str(netid)}";""")
    user_exists = cursor.fetchone()[0] > 0
    return user_exists

############################################ INSERTS ############################################
def enter_user(netid, name, year, credithours, preferenceID, majorname):
    con = open_connection()
    cursor = con.cursor()
    data = [(netid, name, year, credithours, preferenceID, majorname)]
    cursor.executemany("INSERT INTO User (NetID, Name, Year, CreditHours, PreferenceID, MajorName) VALUES (%s, %s, %s, %s, %s, %s)", data)
    con.commit()

def enter_enrollments(netid, subject, coursenumber):
    con = open_connection()
    cursor = con.cursor()
    data = [(netid, subject, coursenumber)]
    cursor.executemany("INSERT INTO Enrollments (NetID, Subject, CourseNumber) VALUES (%s, %s, %s)", data)
    con.commit()

def enter_preferences(preference_id, gpa_weight, professor_weight, credits_weight, netid):
    con = open_connection()
    cursor = con.cursor()
    data = [(preference_id, gpa_weight, professor_weight, credits_weight, netid)]
    cursor.executemany("INSERT INTO Preference (PreferenceID, GPAWeight, ProfessorWeight, CreditsWeight, NetID) VALUES (%s, %s, %s, %s, %s)", data)
    con.commit()

############################################ DELETE ############################################

def delete_user(netid):
    con = open_connection()
    cursor = con.cursor()
    cursor.execute(f"""DELETE From User Where User.NetID = "{str(netid)}";""")
    con.commit()

# def delete_enrollments(netid):
#     con = open_connection()
#     cursor = con.cursor()
#     cursor.execute(f"""DELETE From Enrollments Where Enrollments.NetID = "{str(netid)}";""")
#     con.commit()

# def delete_preferences(netid):
#     con = open_connection()
#     cursor = con.cursor()
#     cursor.execute(f"""DELETE From Preference Where Preference.NetID = "{str(netid)}";""")
#     con.commit()

############################################ UPDATE ############################################
def update_preferences(gpa_weight, professor_weight, credits_weight, netid):
    con = open_connection()
    cursor = con.cursor()
    query_update = """
        UPDATE Preference
        SET GPAWeight = %s, ProfessorWeight = %s, CreditsWeight = %s
        WHERE PreferenceID = (SELECT PreferenceID FROM User WHERE NetID = %s);
    """
    cursor.execute(query_update, (gpa_weight, professor_weight, credits_weight, netid))
    con.commit()


# def update_preferences(gpa_weight, professor_weight, credits_weight, netid):
#     try: 
#         con = open_connection()
#         cursor = con.cursor()
#         query_check = "SELECT COUNT(*) FROM User WHERE NetID = %s"
#         cursor.execute(query_check, (netid,))
#         user_exists = cursor.fetchone()[0] > 0
#         if user_exists:
#             cursor.execute("BEGIN TRANSACTION")
#             query_update = """
#                 UPDATE Preference
#                 SET GPAWeight = %s, ProfessorWeight = %s, CreditsWeight = %s
#                 WHERE PreferenceID = (SELECT PreferenceID FROM User WHERE NetID = %s);
#             """
#             cursor.execute(query_update, (gpa_weight, professor_weight, credits_weight, netid))
#             cursor.execute("COMMIT;")
#             con.commit()
#     except Exception as e:
#         cursor.execute("ROLLBACK;")


############################################ READ ############################################
def return_query(netid, rank_one, rank_two, rank_three, rank_four):
    con = open_connection()
    cursor = con.cursor()
    cursor.execute(f"""CALL GetCourseInfo("{netid}", "{rank_one}", "{rank_two}", "{rank_three}")""")
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(results, columns=columns)
    return df


def recommendation_query(df, subject):
    return df[df['Subject'] == str(subject)]


def get_user_data(netid):
    con = open_connection()
    cursor = con.cursor()
    cursor.execute(f"""CALL GetUserPreferencesWithEnrollments("{netid}")""")
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(results, columns=columns)
    return df