import email
import enum
import re
from crypt import methods
from datetime import datetime
from email.policy import default
from enum import unique
from fileinput import filename
from os.path import join
from sqlite3 import IntegrityError

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from utils import *

# app = Flask(__name__)
# app.config['SECRET_KEY'] = '0f69a7a5ce13f3e8611970e73fca73f6'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# db = SQLAlchemy(app)



app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['UPLOAD_FOLDER'] = 'static/images'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'r00tr00t'
app.config['MYSQL_DB'] = 'HSTU_Social'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# def create_app():
#     app = Flask(__name__)

#     with app.app_context():
        
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
#         app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#         db = SQLAlchemy(app)
#     return app


@app.route("/")
@app.route("/feed")
def feed():

    if 'sid' not in session:
        return redirect("/signup")
    
    sid = session["sid"]

    cursor = mysql.connection.cursor()
    cursor.execute("""
    Select post.* , Student.*
    FROM post INNER JOIN Student 
    ON post.author = Student.sid;
    """)

    posts = cursor.fetchall()
    
    print(posts)

    # print(posts)

    cursor.execute("""
    SELECT *
    FROM Student
    WHERE sid = {}
    """.format(sid)
    )

    user_details = cursor.fetchall()[0]
    # print("printing user details")
    # print(user_details)

    cursor.execute("""
        SELECT * FROM HSTU_Social.blood_donation;
        """
        )

    blood_donations = cursor.fetchall()


    cursor.execute("""
        SELECT * FROM HSTU_Social.lost_n_found;
        """
        )

    lost_n_founds = cursor.fetchall()
    cursor.close()


    print("printing the query.............")
    print(posts[1]['photo1'])
    print(posts[1]['photo2'])


    # for bd in blood_donations:
    #     for i in bd:
    #         print(i)


    #         print(f"{i} --- > {p}")
    # l = [x for x in range(10)]


   
    return render_template('index.html', posts = posts, user = user_details, blood_donations = blood_donations, lost_n_founds =  lost_n_founds) 

@app.route("/signup")
def signup():
    # flash("demo flash", "error")
    return render_template('signup.html')


@app.route("/signup_validate", methods =  ['POST'])
def signup_validate():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    department = request.form.get('department')
    faculty = request.form.get('faculty')
    sid = request.form.get('sid')
    phone_no = request.form.get('phone_no')
    blood_group = request.form.get('blood_group')


    print(type(name), email, type(password), department, faculty, sid, phone_no)

    if not password_validator(password):

        flash("Invalid Passowrd", "error")
        return redirect("/signup")

    if not email_validator(email):

        flash("Invalid Email", "error")
        return redirect("/signup")

    if not sid_validator(sid):

        flash("Invalid SID", "error")
        return redirect("/signup")

    if department is None:
        flash("PLease Select a Department", "error")
        return redirect("/signup")
    if faculty is None:
        flash("PLease Select a Faculty", "error")
        return redirect("/signup")
    if phone_no is None:
        flash("PLease give a phone_no", "error")
        return redirect("/signup")

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
        INSERT INTO `HSTU_Social`.`Student` (`sid`, `email`, `password`, `name`, `pro_pic`, `department`, `faculty`, `phone_no`, `blood_group`)
        VALUES 
        ( '{}',  '{}',  '{}',  '{}', NULL ,  '{}',  '{}',  '{}',  '{}');

        """.format(sid, email, pw_hash, name, department, faculty, phone_no, blood_group ))


        mysql.connection.commit()
        cursor.close()

    except mysql.connection.IntegrityError as e:
        print("erooooooooooooor")
        # print(tuple(e))
        
        # print(err)
        # print("Error Code:", err.errno)
        # print("SQLSTATE", err.sqlstate)
        # print("Message", err.msg)
        # flash(err.msg, "error")
        flash(e.args[1], "error")

        return redirect("/signup")

    
    # cursor.close()
    # print(f"this is Hasshed password {pw_hash} ---> {type(pw_hash)}")
    return "success"



@app.route("/login_validate", methods =  ['POST'])
def login_validate():

    email = request.form.get('email')
    password = request.form.get('password')
    cursor = mysql.connection.cursor()
    cursor.execute("""
    SELECT sid, email, password 
    FROM `HSTU_Social`.`Student`
    WHERE `email` = '{}'
    """.format(email)
    )

    data = cursor.fetchall()

    if len(data) == 0:
        print(data)
        print(email)
        flash("Email Address is not found")
        return redirect("/signup")

    pw_hash = data[0]["password"]
    print(password)

    if bcrypt.check_password_hash(pw_hash, password):
        session["sid"] = data[0]["sid"]
        return redirect("/feed")

    else:
        flash("Incorrect Password")
        return redirect("/signup")



@app.route("/logout")
def logout():
    session.pop('sid')
    return redirect('/signup')


@app.route("/create_post", methods = ['POST'])
def create_post():
    sid = session["sid"]

    # print("create app section")

    content = request.form.get("content")
    type = "Personal"

    photo1_filename = ''
    photo2_filename = ''

    photo1 = request.files['photo1']
    
    if len(photo1.filename) != 0:
        photo1_filename = secure_filename(photo1.filename)
        print('photo1 found')
        print(photo1_filename)
        photo1.save(join(app.config['UPLOAD_FOLDER'], photo1_filename))

    photo2 = request.files['photo2']
    
    if len(photo2.filename) != 0:
        photo2_filename = secure_filename(photo2.filename)
        print('photo2 found')
        print(photo2_filename)
        photo2.save(join(app.config['UPLOAD_FOLDER'], photo2_filename))


    # print(photo1)
    # print(photo2)
    
    
    # print(photo1_filename)
    print(photo2_filename)
    # print(type(photo2_filename))
    print(len(photo2_filename))



    

    # print(content)
    # type = request.form.get("type")
    

    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
        """
        INSERT INTO `HSTU_Social`.`post` 
        (`content`, `author`, `type`, photo1, photo2) 
        VALUES 
        ('{}', '{}', '{}', NULLIF('{}', ''), NULLIF('{}', '') );
        """.format(content, sid, type, photo1_filename, photo2_filename)
        )

        mysql.connection.commit()
        cursor.close()
# print(%d %d %d, a,b,v)

    except mysql.connection.IntegrityError as e:
        print("erooooooooooooor")
      
        flash(e.args[1], "error")

        return redirect("/feed")


    return redirect("/feed")


@app.route("/create_blood_donation", methods = ['POST', 'GET'])
def create_blood_donation():

    if 'sid' not in session:
        return redirect("/signup")


    sid = session["sid"]
    if request.method == 'GET':
        
        return render_template("create_blood_donation.html")
    
    place = request.form.get("place")
    time = request.form.get("time")
    print(type(time))
    print(time)
    group = request.form.get("group")
    no_of_bag = request.form.get("no_of_bag")
    details = request.form.get("details")
    time = time.replace("T", " ")
    # time+=":00"
    print(time)
    print(place, time, group, no_of_bag, details)

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `HSTU_Social`.`blood_donation` 
            (`group`, `place`, `donation_time`, `no_of_bag`, `author`, `details`) 
            VALUES 
            ('{}', '{}', '{}', '{}', '{}','{}');

            """.format(group, place, time, no_of_bag, sid, details)
        )
        mysql.connection.commit()
        cursor.close()

        return redirect("/feed")

    except mysql.connection.IntegrityError as e:
            print("erooooooooooooor")

            print(e.args[1])
            flash(e.args[1], "error")
            return redirect("/create_blood_donation")
    

@app.route("/create_lost_n_found", methods = ['POST', 'GET'])
def lost_n_found():

    if 'sid' not in session:
        return redirect("/signup")


    sid = session["sid"]
    if request.method == 'GET':
        
        return render_template("lost_n_found.html")
    
    place = request.form.get("place")
    time = request.form.get("time")
    item = request.form.get("item")
    print(type(time))
    print(time)


    details = request.form.get("details")
    time = time.replace("T", " ")
    # time+=":00"
    print(time)
    print(place, time, details)

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `HSTU_Social`.`lost_n_found` 
            (`place`, `time`, `author`, `details`, `item`) 
            VALUES 
            ('{}', '{}', '{}', '{}', '{}');

            """.format(place, time, sid, details, item)
        )
        mysql.connection.commit()
        cursor.close()

        return redirect("/feed")

    except mysql.connection.IntegrityError as e:
            print("erooooooooooooor")

            print(e.args[1])
            flash(e.args[1], "error")
            return redirect("/create_blood_donation")
    
@app.route("/like_post/<post_id>/", )
def like_post(post_id):

    sid = session['sid']
    post_id = post_id
    print("------Like Function Called")
    print(sid, post_id)
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `HSTU_Social`.`like` 
            (`author`, `post`) 
            VALUES 
            ('{}', '{}');

            """.format(sid, post_id)
        )

        
        cursor.execute(
            """
            SELECT count(id)
            FROM `HSTU_Social`.`like` 
            WHERE post = {}
            """.format(post_id)
        ) 
        like_count = cursor.fetchall()[0]['count(id)']
        print(like_count)

        cursor.execute(
            """
            UPDATE `HSTU_Social`.`post` 
            SET `like` = '{}' 
            WHERE (`id` = '{}');

            """.format(like_count, post_id)
        )

        mysql.connection.commit()
        cursor.close()

        d = {
            "like_count": like_count,
        }
        return jsonify(d)

    except mysql.connection.IntegrityError as e:
            print("erooooooooooooor")

            print(e.args[1])
            flash(e.args[1], "error")
            return redirect("/feed")



@app.route("/dislike_post/<post_id>/", )
def dislike_post(post_id):

    sid = session['sid']
    post_id = post_id
    print("------disLike Function Called")
    print(sid, post_id)
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `HSTU_Social`.`dislike` 
            (`author`, `post`) 
            VALUES 
            ('{}', '{}');

            """.format(sid, post_id)
        )

        cursor.execute(
            """
            SELECT count(id)
            FROM `HSTU_Social`.`dislike` 
            WHERE post = {}
            """.format(post_id)
        ) 
        dislike_count = cursor.fetchall()[0]['count(id)']
        print(dislike_count)

        cursor.execute(
            """
            UPDATE `HSTU_Social`.`post` 
            SET `dislike` = '{}' 
            WHERE (`id` = '{}');

            """.format(dislike_count, post_id)
        )

        mysql.connection.commit()
        cursor.close()

        d = {
            "dislike_count": dislike_count,
        }
        return jsonify(d)

    except mysql.connection.IntegrityError as e:
            print("erooooooooooooor")

            print(e.args[1])
            flash(e.args[1], "error")
            return redirect("/feed")
    
@app.route("/profile")
def profile():
    if 'sid' not in session:
        return redirect("/signup")
    
    sid = session["sid"]

    cursor = mysql.connection.cursor()
    # cursor.execute("""
    # Select post.* , Student.name
    # FROM post INNER JOIN Student 
    # ON post.author = Student.sid;
    # """)

    cursor.execute(
        """
        Select *
        from post
        where author = '{}'
        """.format(sid)
    )
    posts = cursor.fetchall()


    cursor.execute(
        """
        Select student.name , Student.sid
        FROM HSTU_Social.relationship INNER JOIN HSTU_Social.Student 
        ON relationship.follower = Student.sid
        WHERE relationship.following = '{}'; 
        """.format(sid)
    )
    followers = cursor.fetchall()
    print(followers[0])

    cursor.execute(
        """
        Select student.name , Student.sid
        FROM HSTU_Social.relationship INNER JOIN HSTU_Social.Student 
        ON relationship.following = Student.sid
        WHERE relationship.follower = '{}'; 
        """.format(sid)
    )
    followings = cursor.fetchall()
    print(followings[0])


    cursor.execute("""
    SELECT *
    FROM Student
    WHERE sid = {}
    """.format(sid)
    )

    user_details = cursor.fetchall()[0]
  

    cursor.execute("""
        SELECT * 
        FROM HSTU_Social.blood_donation
        WHERE author = '{}';
        """.format(sid)
        )

    blood_donations = cursor.fetchall()

    cursor.close()



    print(blood_donations)


    return render_template('profile_custom.html',
     posts = posts, 
     user = user_details, 
     blood_donations = blood_donations,
     followers = followers,
     followings = followings,
      ) 

@app.route("/other_profile/<sid>/")
def other_profile(sid):
    cursor = mysql.connection.cursor()
    # cursor.execute("""
    # Select post.* , Student.name
    # FROM post INNER JOIN Student 
    # ON post.author = Student.sid;
    # """)
    mysid = str(session["sid"])

    if sid == mysid:
        return redirect('/profile')
    
    # !========================  Posts ======================== #
    cursor.execute(
        """
        Select *
        from post
        where author = '{}'
        """.format(sid)
    )
    posts = cursor.fetchall()


# !======================== user details ======================== #
    cursor.execute("""
    SELECT *
    FROM Student
    WHERE sid = {}
    """.format(sid)
    )

    user_details = cursor.fetchall()[0]
  
    # !======================== Blood Donation ======================== #
    cursor.execute("""
        SELECT * 
        FROM HSTU_Social.blood_donation
        WHERE author = '{}';
        """.format(sid)
        )

    blood_donations = cursor.fetchall()

    # !======================== Lost and Found ======================== #
    cursor.execute("""
        SELECT * 
        FROM HSTU_Social.lost_n_found
        WHERE author = '{}';
        """.format(sid)
        )

    lost_n= cursor.fetchall()

    # !======================== Events ======================== #
    cursor.execute("""
        SELECT * 
        FROM HSTU_Social.event
        WHERE author = '{}';
        """.format(sid)
        )

    blood_donations = cursor.fetchall()


    # !======================== Follow Unfollow ======================== #
    cursor.execute("""
        SELECT * 
        FROM HSTU_Social.relationship
        WHERE following = '{}' AND follower = '{}';
        """.format(sid, mysid)
        )

    follow_fetch = cursor.fetchall()
    print(len(follow_fetch))
    if len(follow_fetch):
        user_details['isfollow'] = True
    else:
        user_details['isfollow'] = False 
    # print(user_details)
   



# !======================== Followers and Following ======================== #
    cursor.execute(
        """
        Select student.name , Student.sid
        FROM HSTU_Social.relationship INNER JOIN HSTU_Social.Student 
        ON relationship.follower = Student.sid
        WHERE relationship.following = '{}'; 
        """.format(sid)
    )
    followers = cursor.fetchall()
    print(followers[0])

    cursor.execute(
        """
        Select student.name , Student.sid
        FROM HSTU_Social.relationship INNER JOIN HSTU_Social.Student 
        ON relationship.following = Student.sid
        WHERE relationship.follower = '{}'; 
        """.format(sid)
    )
    followings = cursor.fetchall()
    print(followings[0])

    cursor.close()
    return render_template('other_profile.html', 
    posts = posts, 
    user = user_details, 
    blood_donations = blood_donations,
    followers = followers,
    followings = followings,
    )



@app.route("/follow/<sid>/", )
def follow(sid):
    print(sid)
    mysid = session['sid']
    
    print(f"{mysid} Unfollowing {sid}")
    
    
    cursor = mysql.connection.cursor()
    cursor.execute(
    """
    INSERT INTO `HSTU_Social`.`relationship`
    (`follower`, `following`)
    VALUES
    ('{}', '{}')
    """.format(mysid, sid)
    )

    mysql.connection.commit()
    cursor.close()

    return redirect("/other_profile/"+sid)

@app.route("/unfollow/<sid>/", )
def unfollow(sid):

    mysid = session['sid']

    print(f"{mysid} Unfollowing {sid}")

    
    

    cursor = mysql.connection.cursor()
    cursor.execute(
    """
    DELETE FROM `HSTU_Social`.`relationship` 
    WHERE (`follower` = '{}') and (`following` = '{}');

    """.format(mysid, sid )
    )

    mysql.connection.commit()
    cursor.close()
    return redirect("/other_profile/"+sid)



@app.route("/stat")
def stat():

    
    return render_template("stat.html",)




@app.route("/stat_data/")
def stat_data_collector():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT * 
        FROM HSTU_Social.student;
        """
    )

    student_stat = cursor.fetchall()

    cursor = mysql.connection.cursor()
    cursor.execute("""
    Select post.* , Student.gender
    FROM post INNER JOIN Student 
    ON post.author = Student.sid;
    """)

    post_stat = cursor.fetchall()


    # cursor = mysql.connection.cursor()
    # cursor.execute("""
    #     SELECT * 
    #     FROM HSTU_Social.comment;
    #     """
    # )

    # comment_stat = cursor.fetchall()
    no_of_male = 0
    no_of_female = 0
    for ss in student_stat:
        # print(ss['gender'])
        if ss['gender'] == 1 :
            no_of_male +=1

            print(ss['name'], 'male', no_of_male)
        else:
            no_of_female+=1

            print(ss['name'], 'female', no_of_female)

    post_male = 0
    post_female = 0

    for ps in post_stat:
        print(ps['gender'])
        if ps['gender'] ==1:
            post_male+=1
        else:
            post_female +=1


    # print(ss)
    # print(student_stat)
    # print(male, female)
    no_of_users = len(student_stat)
    no_of_posts = len(post_stat)
    no_of_comments = 0
    

    data = {
        "user_count": no_of_users,
        "post_count": no_of_posts,
        "gender": [no_of_male, no_of_female],
        "post_gender": [post_male, post_female],
        "comment_count": no_of_comments,
    }

    return jsonify(data)



# !=========================================================
if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug = True, host='0.0.0.0', port=5690)

