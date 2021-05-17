from flask import Flask, render_template, redirect, url_for, request, send_from_directory, session, abort, Response, jsonify, flash
import os
import mysql.connector
import hashlib
import datetime
import time, json
from mysql.connector import errorcode

app = Flask(__name__)
app.secret_key = '\x8f\x95\xf6w\xb5\xcaME\xe0w\x8f\xcb\xdf\xedp\x0c\x19|\xbe\xaa\xab\x08]\xb2'

config = {
  'user': 'root',
  'password': 'Tango527',
  'host': '127.0.0.1',
  'database': 'comp5013',
}

mydb = mysql.connector.connect(**config) # SQL connection
mycursor = mydb.cursor(dictionary=True)

@app.route('/')
def index():
    # Check if user is logged in
    sql = 'SELECT title,author,claims FROM topics'
    mycursor.execute(sql)  
    topics = mycursor.fetchall()
    if 'user' in session:
        user = session['user']
        return render_template('index.html', user=user, topics=topics)
    return render_template('index.html', user=None, topics=topics)

@app.route('/sorting', methods=['GET','POST'])
def sorting():
    sortingType = request.form['sortingType']

    if sortingType == 'latest':
        session['sortingType'] = 'latest'
    elif sortingType == 'popular':
        session['sortingType'] = 'popular'
    elif sortingType == 'rising':
        session['sortingType'] = 'rising'
    return redirect(url_for('topic', topic_title=request.form['topicID']))

@app.route('/topic/<topic_title>', methods=['GET', 'POST'])
def topic(topic_title):
    user, interactions, claims, sortingType, username = None, None, None, None, None
    sql = 'SELECT * FROM topics WHERE title =%s'
    val = (topic_title,)
    mycursor.execute(sql, val)
    topic = mycursor.fetchall()

    if 'user' in session:
        user = session['user']
        username = user['username']
        sql = 'SELECT * FROM interactions WHERE topic_id =%s AND user=%s'
        val = (topic[0]['id'],user['username'],)
        mycursor.execute(sql, val)
        interactions = mycursor.fetchall()

    if 'sortingType' in session:
        sortingType = session['sortingType']
        if sortingType == 'latest':
            sql = 'SELECT * FROM claims WHERE topic_id =%s ORDER BY timestamp desc' # Sort Latest
            val = (topic[0]['id'],)
            mycursor.execute(sql, val)
            claims = mycursor.fetchall()
        elif sortingType == 'popular':
            sql = 'SELECT * FROM claims WHERE topic_id =%s ORDER BY total_likes desc, total_comments desc' # Sort Popular
            val = (topic[0]['id'],)
            mycursor.execute(sql, val)
            claims = mycursor.fetchall()
        elif sortingType == 'rising':
            sql = 'SELECT * FROM claims WHERE topic_id =%s AND timestamp >= DATE_SUB(NOW(), INTERVAL "8" HOUR) ORDER BY total_comments desc, total_likes desc' # Sort Rising
            val = (topic[0]['id'],)
            mycursor.execute(sql, val)
            claims = mycursor.fetchall()
    else:
        sql = 'SELECT * FROM claims WHERE topic_id =%s'
        val = (topic[0]['id'],)
        mycursor.execute(sql, val)
        claims = mycursor.fetchall()

    return render_template('claims.html', user=user, topic=topic, claims=claims, interactions=interactions,
                            sorting=sortingType, admin=checkAdmin(username,topic[0]['id']), topic_owner=checkTopicOwner(username,topic[0]['id']) )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

#Authentication

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    formUsername = request.form['username']
    formPassword = request.form['password']
    
    mydb = mysql.connector.connect(**config) # SQL connection
    mycursor = mydb.cursor(dictionary=True)
    sql = 'SELECT * FROM users WHERE username =%s'
    val = (formUsername,)
    mycursor.execute(sql, val)
    user = mycursor.fetchall()
    
    if(user):
        user = user[0]
        password = user["password"]
        hashedFormPassword = hashlib.sha256(str(formPassword).encode('utf-8'))
        if(password == hashedFormPassword.hexdigest()):
            # create session
            user.pop("password")
            session['user'] = user
            return redirect(url_for('index'))
        else:
            flash('Password is incorrect.')
            return redirect('/')

    flash('User doesn\'t exist.')
    return redirect('/')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if request.form['password'] == request.form['confirmPassword']:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            hashed = hashlib.sha256(str(password).encode('utf-8')) # Hash Password
            if len(password) >= 6:
                mydb = mysql.connector.connect(**config) # SQL connection
                mycursor = mydb.cursor()

                sql = 'SELECT * FROM users WHERE username =%s'
                val = (username,)
                mycursor.execute(sql, val)
                user = mycursor.fetchall()

                if not user:
                    sql = "INSERT INTO users (email,username,password) VALUES (%s, %s, %s)" # SQL query
                    val = (email, username, hashed.hexdigest())
                    mycursor.execute(sql, val) # Query execution
                    mydb.commit()
                else:
                    flash('Username Exists')
            else:
                flash('Password shorter than 6 characters')
        else:
            flash('Passwords don\'t match.')
    return redirect('/')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect('/')
#Authentication

@app.route('/create-topic', methods=['GET', 'POST'])
def createTopic():
    if 'user' in session:
        topicTitle = request.form['title'].lower()
        topicDescription = request.form['description']
        sql = 'SELECT * FROM topics WHERE title =%s'
        val = (topicTitle,)
        mycursor.execute(sql, val)
        topic = mycursor.fetchall()

        if not topic:
            user = mycursor.fetchall()
            user = session['user']
            timestamp = round(time.time())

            sql = "INSERT INTO topics (title,description,claims,date,author) VALUES (%s, %s, %s, %s, %s)" # SQL query
            val = (topicTitle,topicDescription,0,timestamp,user['username'])
            mycursor.execute(sql, val) # Query execution
            mydb.commit()

            sql = 'SELECT * FROM topics WHERE title =%s'
            val = (topicTitle,)
            mycursor.execute(sql, val)
            topic = mycursor.fetchall()

            sql =  "INSERT INTO admin (username,topic_id,topic_owner) VALUES (%s, %s, %s)" # Make user admin
            val = (user['username'],topic[0]['id'],1)
            mycursor.execute(sql, val) # Query execution
            mydb.commit()

            return redirect('/')
        else:
            flash("Topic already exists")
            return redirect('/')
    else:
        flash("You need to be logged in to do that.")
        return redirect('/')

@app.route('/create-claim', methods=['GET', 'POST'])
def createClaim():
    topicID = request.form['topic-id']
    sql = 'SELECT title FROM topics WHERE id =%s'
    val = (topicID,)
    mycursor.execute(sql, val)
    topic = mycursor.fetchall()
    
    if 'user' in session:
        user = session['user']
        claimTitle = request.form['title']
        claimDescription = request.form['description']
        
        date = round(time.time() * 1000) # Get Date
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') # For sorting

        if 'related_claim_id' in request.form and request.form['related_claim_id'] != '': # If claim is related
            relatedID = request.form['related_claim_id']
            sql = "INSERT INTO claims (author,title,topic_id,relates_to,description,date,timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)" # SQL query
            val = (user['username'],claimTitle,topicID,relatedID,claimDescription,date,timestamp)
        else:
            sql = "INSERT INTO claims (author,title,topic_id,description,date,timestamp) VALUES (%s, %s, %s, %s, %s, %s)" # SQL query
            val = (user['username'],claimTitle,topicID,claimDescription,date,timestamp )
        
        mycursor.execute(sql, val) # Query execution
        mydb.commit()

        sql = "UPDATE topics set claims = (claims + 1) WHERE id =%s" # Add amount of claims to topic
        val = (topicID,)
        mycursor.execute(sql, val) # Query execution
        mydb.commit()
        return redirect(url_for('topic', topic_title=topic[0]['title']))
    else:
        flash("You need to be logged in to do that.")
        return redirect(url_for('topic', topic_title=topic[0]['title']))

@app.route('/interaction', methods=['GET', 'POST'])
def interaction():

    if 'user' in session:
        formLike = int(request.form['like'])
        formDislike = int(request.form['dislike'])
        claimID = int(request.form['id'])
        topicID = int(request.form['topic_id'])
        user = session['user']
        
        sql = "SELECT * FROM interactions WHERE user =%s AND claim_id=%s"
        val = (user['username'],claimID)
        mycursor.execute(sql, val)
        interaction = mycursor.fetchall()
        
        if not interaction:
            val = (formLike,formDislike,user['username'],claimID, topicID)
            mycursor.execute("INSERT INTO interactions (claim_like,claim_dislike,user,claim_id,topic_id) VALUES (%s,%s,%s,%s,%s)", val)
            mydb.commit()
            if formLike:
                sql = "UPDATE claims SET total_likes = (total_likes + 1) WHERE id =%s"
                val = (claimID,)
            else:
                sql = "UPDATE claims SET total_dislikes = (total_dislikes + 1) WHERE id =%s"
                val = (claimID,)
            mycursor.execute(sql, val)
            mydb.commit()
            return "success"

        elif (formLike and interaction[0]['claim_like']) or (formDislike and interaction[0]['claim_dislike']): # UNLIKE OR UNDISLIKE
            sql = "UPDATE interactions SET claim_like =%s, claim_dislike =%s WHERE user =%s AND claim_id=%s"
            val = (0,0,user['username'],claimID,)
            mycursor.execute(sql, val)
            mydb.commit()

            if formLike:
                sql = "UPDATE claims SET total_likes = (total_likes - 1) WHERE id =%s"
                val = (claimID,)
            else:
                sql = "UPDATE claims SET total_dislikes = (total_dislikes - 1) WHERE id =%s"
                val = (claimID,)
            mycursor.execute(sql, val)
            mydb.commit()
            return "success"
       
        else: # If Interaction already exists, update it
            sql = "UPDATE interactions SET claim_like =%s, claim_dislike =%s WHERE user =%s AND claim_id=%s"
            val = (formLike,formDislike,user['username'],claimID,)
            mycursor.execute(sql, val)
            mydb.commit()
           
            if formLike:
                if interaction[0]['claim_dislike'] != 0:
                    sql = "UPDATE claims SET total_dislikes = (total_dislikes - 1) WHERE id =%s"
                    val = (claimID,)
                    mycursor.execute(sql, val)
                    mydb.commit()
                sql = "UPDATE claims SET total_likes = (total_likes + 1) WHERE id =%s"
                val = (claimID,)
                
            else:
                if interaction[0]['claim_like'] != 0:
                    sql = "UPDATE claims SET total_likes = (total_likes - 1) WHERE id =%s"
                    val = (claimID,)
                    mycursor.execute(sql, val)
                    mydb.commit()
                sql = "UPDATE claims SET total_dislikes = (total_dislikes + 1) WHERE id =%s"
                val = (claimID,)
               
            mycursor.execute(sql, val)
            mydb.commit()
          
            return "success"
        
def get_children(comment):

    commentID = int(comment['id'])
    sql = 'SELECT * FROM replies WHERE reply_id=%s' 
    val = (commentID,)
    mycursor.execute(sql, val)
    children = mycursor.fetchall()

    if(len(children)):
        this_children = []
        for child in children:
            this_children.append(get_children(child))
        
        return { "data" : comment, "reply" : this_children}
    else:
        return comment

@app.route('/claim/<claim_id>', methods=['GET', 'POST'])
def claim(claim_id):
    sql = 'SELECT * FROM claims WHERE id =%s'
    val = (claim_id,)
    mycursor.execute(sql, val)
    claim = mycursor.fetchall()

    sql = 'SELECT * FROM replies WHERE claim_id =%s'
    val = (claim_id,)
    mycursor.execute(sql, val)
    comments = mycursor.fetchall()

    replies = []
    for comment in comments:
        replies.append(get_children(comment))

    comments = replies
    
    if 'user' in session:
        user = session['user']

        sql = 'SELECT * FROM interactions WHERE claim_id =%s AND user=%s'
        val = (claim_id,user['username'],)
        mycursor.execute(sql, val)
        interactions = mycursor.fetchall()

        return render_template('claim.html', user=user, claim=claim, interactions=interactions, comments=comments, 
        admin=checkAdmin(user['username'],claim[0]['topic_id']), topic_owner=checkTopicOwner(user['username'],claim[0]['topic_id']))

    return render_template('claim.html', user=None, claim=claim, comments=comments)

@app.route('/claim/<claim_id>/comment', methods=['GET', 'POST'])
def comment(claim_id):
    if 'user' in session:
        formComment = request.form['comment']
        replyType = request.form['reply-type']
        replyTypes = ['supporting', 'counter','clarification', 'support', 'evidence', 'rebuttal']
        claimId = claim_id
        user = session['user']

        if replyType not in replyTypes:
            replyType = None

        if 'reply_id' in request.form: # A reply
            replyID = request.form['reply_id']

            mycursor = mydb.cursor()
            sql = "INSERT INTO replies (reply_id,username,claim_id,comment,reply_type) VALUES (%s, %s, %s, %s, %s)" # SQL query
            val = (replyID,user['username'],claimId,formComment,replyType,)
            mycursor.execute(sql, val) # Query execution
            mydb.commit()
        
            sql = "UPDATE claims SET total_comments = (total_comments + 1) WHERE id =%s" # Update total commentss
            val = (claimId,)
            mycursor.execute(sql, val) # Query execution
            mydb.commit()

            return redirect('/claim/'+claim_id)
        
        mycursor = mydb.cursor()
        sql = "INSERT INTO replies (username,claim_id,comment,reply_type) VALUES (%s, %s, %s,%s)" # SQL query
        val = (user['username'],claimId,formComment,replyType,)
        mycursor.execute(sql, val) # Query execution
        mydb.commit()
    
        sql = "UPDATE claims SET total_comments = (total_comments + 1) WHERE id =%s"
        val = (claimId,)
        mycursor.execute(sql, val) # Query execution
        mydb.commit()

        return redirect('/claim/'+claim_id)
    else:
        flash("You need to be logged in to do that.")
        return redirect('/claim/'+claim_id)

def checkKey(dict, key):
      
    if key in dict.keys():
        return True
    else:
        return False

@app.route('/claim/<claim_id>/get-comments')
def getComments(claim_id):
    sql = 'SELECT * FROM replies WHERE claim_id =%s'
    val = (claim_id,)
    mycursor.execute(sql, val)
    comments = mycursor.fetchall()
    return jsonify(comments)

@app.route('/search', methods=['GET', 'POST'])
def search():
    user = None
    search = '%'+request.form['query']+'%'
    mydb = mysql.connector.connect(**config) # SQL connection
    mycursor = mydb.cursor(dictionary=True)
    sql = 'SELECT * FROM claims WHERE title LIKE %s'
    val = (search,)
    mycursor.execute(sql, val)
    results = mycursor.fetchall()
    
    if 'user' in session:
        user = session['user']
    return render_template('searchResults.html', claims=results, user=user)

@app.errorhandler(401)
def error401(error):
    return render_template('401Page.html'), 401

@app.errorhandler(404)
def error404(e):
  return render_template('404Page.html'), 404
# def loginFrom401():


def checkAdmin(username, topic_id):
    mydb = mysql.connector.connect(**config) # SQL connection
    mycursor = mydb.cursor(dictionary=True)
    sql = 'SELECT * FROM admin WHERE username =%s and topic_id =%s'
    val = (username,topic_id)
    mycursor.execute(sql, val)
    check = mycursor.fetchall()
    if check:
        return 1
    else:
        return 0

def checkTopicOwner(username, topic_id):
    mydb = mysql.connector.connect(**config) # SQL connection
    mycursor = mydb.cursor(dictionary=True)
    sql = 'SELECT * FROM admin WHERE username =%s and topic_id =%s'
    val = (username,topic_id)
    mycursor.execute(sql, val)
    check = mycursor.fetchall()
    if check and check[0]['topic_owner']:
        return 1
    else:
        return 0