from datetime import datetime
import sqlite3
import os
import db1
from flask import Flask,redirect,request,render_template,flash,get_flashed_messages,url_for,make_response
from flask import session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import csv
app=Flask("__name__")
app.secret_key="secret"
categories=["food","shopping","personal","other"]
def get_db_connection():
    conn = sqlite3.connect("exprac.db")
    return conn

@app.route("/",methods=["GET","POST"])
def home():
    if "user_id" not in session:
        flash("Please login","info")
        return redirect("/login")
    user_id=session["user_id"]
    
    page=request.args.get("page",1,type=int)
    limit=5
    offset=(page-1)*limit
    if request.method=="POST":
        title=request.form.get("title").strip()
        amount=request.form.get("amount")
        category=request.form.get("category")
        now=datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            amount=float(amount)
            if amount>0 and 0<len(title)<50 and category in categories:
                conn=get_db_connection()
                cursor=conn.cursor()
                cursor.execute("INSERT INTO exprac (title,amount,category,user_id,created_at) VALUES(?,?,?,?,?)",(title,amount,category,user_id,now))
                conn.commit()
                conn.close()
            else:
                flash("Invalid Input","danger")
        except ValueError:
            flash("Invalid Amount","danger")
        return redirect("/")
    conn=get_db_connection()
    cursor=conn.cursor()
    f_category=request.args.get("f_category")
    f_date=request.args.get("f_date")
    f_search=request.args.get("search")
    query="FROM exprac WHERE user_id=?"
    params=[user_id]
    if f_category:
        query += " AND category=?"
        params.append(f_category)
    search=None
    if f_search:
        search=f"%{f_search}%"
    if search:
        query += " AND title LIKE ?"
        params.append(search)
    if f_date:
        query += " AND strftime('%Y-%m-%d',created_at)=?"
        params.append(f_date)
    cursor.execute("SELECT * " +query+ "ORDER BY created_at DESC LIMIT?  OFFSET?", params+[limit,offset])
    exprac=cursor.fetchall()
    cursor.execute("SELECT COUNT(*) " +query,params)
    total_entries=cursor.fetchone()[0]
    conn.close()
    total_page=(total_entries+limit-1)//limit
    return render_template("index.html",exprac=exprac,categories=categories,page=page,offset=offset,total_page=total_page)
    

@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")
    user_id=session["user_id"]
    if id:
        conn=get_db_connection()
        cursor=conn.cursor()
        cursor.execute("DELETE FROM exprac WHERE id=? AND user_id=?",(id,user_id))
        conn.commit()
        conn.close()
    else:
        flash("Invalid Index","danger")
    return redirect("/")
@app.route("/edit/<int:id>",methods=["GET","POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/login")
    user_id=session["user_id"]
    if id:
        if request.method=="POST":
            title=request.form.get("title").strip()
            amount=request.form.get("amount")
            category=request.form.get("category")
            try:
                amount=float(amount)
                if amount>0 and 0<len(title)<50 and category in categories:
                    conn=get_db_connection()
                    cursor=conn.cursor()
                    cursor.execute("UPDATE exprac SET title=?,amount=?,category=?  WHERE id=? AND user_id=?",(title,amount,category,id,user_id))
                    conn.commit()
                    conn.close()
                    flash("Expese Updated Successfully","succsess" )
                    return redirect("/")
                else:
                    flash("Invalid Input","danger")
            except ValueError:
                flash("Invalid Amount","danger")
            
        conn=get_db_connection()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM exprac WHERE id=? AND user_id=?",(id,user_id))
        expense=cursor.fetchone()
        conn.close()
        if not expense:
            flash("Expense not Found","danger")
            return redirect("/")
    return render_template("edit.html",expense=expense,categories=categories)
@app.route("/signup",methods=["GET","POST"])
def signup():
    if "user_id" in session:
        return redirect("/")
    if request.method=="POST":
        username=request.form.get("username").strip()
        password=request.form.get("password")
        hashed_password= generate_password_hash(password)
        if 0<len(username)<50 and password:
            try:
                conn=get_db_connection()
                cursor=conn.cursor()
                cursor.execute("INSERT INTO users (username,password) VALUEs(?,?)",(username,hashed_password))
                conn.commit()
                conn.close()
                flash("Register Successful","success")
                return redirect("/login")
            except sqlite3.IntegrityError:
                flash("username already exist","info")
        else:
            flash("Invalid Input","danger")
    return render_template("signup.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if "user_id" in session:
        return redirect("/")
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        user=None
        if username and password:
            conn=get_db_connection()
            cursor=conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?",(username,))
            user=cursor.fetchone()
            conn.close()
        if user:
            stored_password=user[2]
            if check_password_hash(stored_password,password):
                session["user_id"]=user[0]
                session["username"]=user[1]
                flash("Login Successful","success")
                return redirect("/")
            else:
                flash("inalid credential","danger")
        else:
            flash("Invalid Credential","danger")
        
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.pop("user_id")
    session.clear()
    return redirect("/login")

       
    
@app.route("/edit_profile",methods=["GET","POST"])
def edit_profile():
    if "user_id" not in session:
        flash("Please login","info")
        return redirect("/login")
    user_id=session["user_id"]
    user_detl=None
    filename=None
    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        dob=request.form.get("dob")
        contact=request.form.get("contact")
        photo = request.files.get("profile_photo")
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
        if 0<len(name)<50 and email and dob and contact:
            conn=get_db_connection()
            cursor=conn.cursor()
            cursor.execute("SELECT profile_photo FROM users WHERE id=?",(user_id,))
            old_photo = cursor.fetchone()[0]
            if filename:
                if old_photo:
                    old_path = "static/upload/" + old_photo
                    if os.path.exists(old_path):
                        os.remove(old_path)
                photo.save("static/upload/" + filename)
                cursor.execute("UPDATE users SET name=?, email=?, profile_photo=?, dob=?, contact=? WHERE id=? ",(name,email,filename,dob,contact,user_id))
            else:
                cursor.execute("UPDATE users SET name=?, email=?, dob=?, contact=? WHERE id=? ",(name,email,dob,contact,user_id))
            conn.commit()
            conn.close()
            flash("Profile Updated Successfully","success")
            return redirect("/profile")
        else:
            flash("Fill detail properly","info")
    
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT name,email,dob,contact,profile_photo FROM users WHERE id=?",(user_id,))
    user_detl=cursor.fetchone()
    conn.close()
    return render_template("edit_profile.html",user_detl=user_detl)
@app.route("/profile")
def profile():
    username=None
    user_info=None   
    user_detl=None
    if "user_id" in session:
        user_id=session["user_id"]
        conn=sqlite3.connect("exprac.db") 
        cursor=conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id=? ",(user_id,))
        username=cursor.fetchone()
        cursor.execute("SELECT SUM(amount),MAX(created_at),COUNT(*) FROM exprac WHERE user_id=? ",(user_id,))
        user_info=cursor.fetchone()
        cursor.execute("SELECT name,email,dob,contact,profile_photo FROM users WHERE id=?",(user_id,))
        user_detl=cursor.fetchone()
        conn.close()
    return render_template("profile.html",username=username,user_info=user_info,user_detl=user_detl)
@app.route("/remove_photo")
def remove_photo():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profile_photo FROM users WHERE id=?",(user_id,))
    photo = cursor.fetchone()[0]
    if photo:
        path = "static/upload/" + photo
        if os.path.exists(path):
            os.remove(path)
        cursor.execute("UPDATE users SET profile_photo=NULL WHERE id=?",(user_id,))
    conn.commit()
    conn.close()
    flash("Profile photo removed", "success")
    return redirect("/edit_profile")          
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    user_id=session["user_id"]
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT SUM(amount), COUNT(*), MAX(amount), MIN(amount) FROM exprac WHERE user_id=?",(user_id,))
    minmax=cursor.fetchone()
    cursor.execute("SELECT * FROM exprac WHERE user_id=? ORDER BY created_at desc LIMIT 4",(user_id,))
    l_entries=cursor.fetchall()
    cursor.execute("SELECT category, SUM(amount) FROM exprac WHERE user_id=? GROUP BY category",(user_id,))
    c_total=cursor.fetchall()
    cursor.execute("SELECT strftime('%Y-%m', created_at),SUM(amount) FROM exprac WHERE user_id=? GROUP BY strftime('%Y-%m', created_at) ORDER BY strftime('%Y-%m', created_at)",(user_id,))
    ym_total=cursor.fetchall()
    conn.close()
        
    return render_template("dashboard.html",minmax=minmax,l_entries=l_entries,c_total=c_total,ym_total=ym_total)

@app.route("/export_csv")
def export_csv():
    if "user_id" not in session:
        return redirect("/login")
    user_id=session["user_id"]
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT title,amount,category,created_at FROM exprac WHERE user_id=?",(user_id,))
    expenses=cursor.fetchall()
    conn.close()
    response=make_response()
    response.headers["Content-Disposition"]="attachment;filename=expenses.csv"
    response.headers["Content-type"]="text/ccsv"
    writer=csv.writer(response.stream)
    writer.writerow(["Title","Amount","Category","Created_at"])
    for expense in expenses:
        writer.writerow(expense)
    return response
if __name__=="__main__":
    app.run(debug=True) 