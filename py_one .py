from flask import Flask, render_template, request, redirect, url_for,session,flash
import mysql.connector
from mysql.connector.errors import IntegrityError

import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import datetime
# import func



# إعداد التطبيق
skill_App = Flask(__name__)

skill_App.secret_key = os.urandom(24)
skill_App.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_key_for_development')


# إعداد المجلد لتخزين الصور
UPLOAD_FOLDER = r'C:\Users\malsa\Desktop\py\static\img'  
skill_App.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# تاريخ  اليوم
def get_date(prm):
 today = datetime.datetime.now()
 day = today.strftime(prm)
 return day
date_today = get_date('%d %b %Y')

# اسم قاعدة البيانات
DATABASE = r'C:\AppServ\MySQL\data\mbl_db'
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # ضع اسم المستخدم الخاص بك
    'password': '123456789',  # ضع كلمة المرور الخاصة بك
    'database': 'mbl_db'  # اسم قاعدة البيانات
}


# الاتصال بقاعدة البيانات
def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn




# دالة لتوليد كلمة سر مشفرة
def hash_password(password):
    return generate_password_hash(password)

# تحقق من صحة البريد الإلكتروني
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@(mbl)+\.(com)+\.(sa)$'
    return re.match(regex, email) is not None
    
# تحقق من صحة  رقم  التلفون
def is_valid_mobile(mobile):
    regex = r'^(0){1}[0-9]{,9}'
    return re.match(regex,mobile) is not None

# تحقق من صحة  رقم  الوظيفي
def is_valid_idnum(idnum):
    regex = r'^([0-9]{4,})$'
    return re.match(regex,idnum) is not None

def RfNameAndLastName(name):
    resit ="".join(name).split(' ')
    last =resit[0] +'  '+ resit[-1]
    return last





# إنشاء جدول قاعدة البيانات
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            Name VARCHAR(255) NOT NULL, 
            idnum INT UNIQUE, 
            email VARCHAR(255) UNIQUE, 
            mobile VARCHAR(15) UNIQUE, 
            password VARCHAR(255) NOT NULL,
            department VARCHAR(255) NOT NULL,
            reid VARCHAR(50) NOT NULL,
            date VARCHAR(50)  NULL,
            image VARCHAR(255)
        )
        """)
        conn.commit()


# استدعاء دالة إنشاء الجدول عند تشغيل التطبيق
init_db()


# صفحة "تسجيل دخول"
@skill_App.route("/", methods=['GET', 'POST'])
def loginpage():
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('password')
        try:
            with get_db_connection() as conn:
                # إعداد المؤشر كـ dictionary
                cursor = conn.cursor(dictionary=True)
                
                # تنفيذ استعلام SQL
                cursor.execute("SELECT * FROM users WHERE idnum = %s", (username,))
                user = cursor.fetchone()  # جلب صف واحد
                
                # التحقق من وجود المستخدم وكلمة المرور
                if user and check_password_hash(user['password'], password):
                    # تخزين اسم المستخدم ومعرفه في الجلسة
                    session['user_id']      = user['id']
                    session['user_idnum']   = user['idnum']
                    session['user_name']    = user['Name']
                    session['user_img']     = user['image']
                    session['reid']         = user['reid']
                    session['mobile_num']   = user['mobile']
                    session['email']        = user['email']
                    session['password_hid']  = user['password_hid']
                    return redirect(url_for('homepage'))
                else:
                    return render_template("login.html",  
                                           pagetitle="login",
                                           style="login",
                                           sidebar='no',
                                           error="Invalid username or password")
        except Exception as e:
            return f"An error occurred: {str(e)}"
    else:
        return render_template("login.html",  
                               pagetitle="login",
                               style="login",
                               sidebar='no')
    

            
# الصفحة الرئيسية
@skill_App.route("/home")
def homepage():
    if 'user_name' in session:
        # استرداد بيانات الجلسة
        user_name = session['user_name']
        user_img = session['user_img']
        reid = session['reid']

        try:
            # الاتصال بقاعدة البيانات
            with get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # تنفيذ استعلام موحد للحصول على جميع الإحصائيات دفعة واحدة
                cursor.execute(
                    """
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE reid != 0) AS total_users,
                        (SELECT COUNT(PC_serial) FROM devices WHERE PC_name = 'dESKTOP') AS total_pc,
                        (SELECT COUNT(PC_serial) FROM devices WHERE PC_name = 'All in one') AS total_All,
                        (SELECT COUNT(PC_serial) FROM devices WHERE PC_name = 'laptop') AS total_laptop,
                        (SELECT COUNT(printer) FROM devices WHERE printer_serial != 'no') AS total_printer,
                        (SELECT COUNT(screan) FROM devices WHERE screan_serial != '') AS total_screan
                    """
                )
                stats = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT 
                        COUNT(CASE WHEN PC_name = 'All in one' THEN 1 END) AS totalpc_all_in_one,
                        COUNT(CASE WHEN PC_name = 'desktop' THEN 1 END) AS totalpc_desktop,
                        COUNT(CASE WHEN PC_name = 'laptop' THEN 1 END) AS totalpc_laptop,
                        COUNT(CASE WHEN screan != 'no' THEN 1 END) AS totalscrean,
                        COUNT(CASE WHEN printer_serial != 'no' THEN 1 END) AS totalprinter
                    FROM devices
                    WHERE idnum = %s
                    """,
                    (session['user_idnum'],)
                )
                user_devices = cursor.fetchone()
                totalpc_all_in_one = user_devices['totalpc_all_in_one'] if user_devices else "0"
                totalpc_desktop = user_devices['totalpc_desktop'] if user_devices else "0"
                totalscrean = user_devices['totalscrean'] if user_devices else "0"
                totalpc_laptop = user_devices['totalpc_laptop'] if user_devices else "0"
                totalprinter = user_devices['totalprinter'] if user_devices else "0"


                # عرض الصفحة مع البيانات المطلوبة
                return render_template(
                    "home.html",
                    pagetitle="لوحة التحكم",
                    style="home",
                    page_head="fa-solid fa-house",
                    userName=RfNameAndLastName(user_name),
                    img=user_img,
                    reid=reid,
                    total_users=stats['total_users'],
                    total_pc=stats['total_pc'],
                    total_printer=stats['total_printer'],
                    total_screan=stats['total_screan'],
                    total_laptop=stats['total_laptop'],
                    total_All=stats['total_All'],
                    totalpc_all_in_one = totalpc_all_in_one,
                    totalpc_desktop = totalpc_desktop,
                    totalscrean = totalscrean,
                    totalpc_laptop = totalpc_laptop,
                    totalprinter = totalprinter
                )

        except Exception as e:
            # تسجيل الخطأ بدلاً من عرضه للمستخدم
            skill_App.logger.error(f"Database error: {e}")
            return render_template("error.html", message="حدث خطأ أثناء تحميل الصفحة."), 500

    else:
        # إذا لم يكن هناك جلسة، إعادة التوجيه إلى صفحة تسجيل الدخول
        return redirect(url_for('loginpage'))

# صفحة المستخدمين
@skill_App.route("/users")
def userspage():
    if 'user_name' in session:
        user_name = session['user_name']
        user_img  = session['user_img']
        reid  = session['reid']
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
        return render_template("users.html",
                               pagetitle="المستخدمين", 
                               style="users", 
                               page_head="fas fa-users",
                               userdata=users,
                               userName=RfNameAndLastName(user_name),
                               img=user_img,reid=reid)
    else:
        return redirect(url_for('loginpage'))


@skill_App.route("/add", methods=['GET', 'POST'])
def addpage():
    if 'user_name' in session:
        user_name = session['user_name']
        user_img = session['user_img']
        reid = session['reid']

        message = None  # رسالة النجاح أو الخطأ
        filename = None  # تعيين قيمة افتراضية للمتغير
        if request.method == 'POST':
            # الحصول على بيانات الفورم
            name = request.form.get('name')
            idnum = request.form.get('idnum')
            email = request.form.get('email')
            mobile = request.form.get('mobile')
            password = request.form.get('password')
            department = request.form.get('department')
            reid = request.form.get('reid')

            # التحقق من وجود الملف
            if 'file' not in request.files:
                message = "يجب رفع ملف الصورة"
            else:
                # الحصول على الملف
                file = request.files['file']
                if file:
                    filename = secure_filename(file.filename)
                    # تأكد من أن هناك اسم للملف
                    if filename:
                        # حفظ الصورة في المجلد المحدد
                        file.save(os.path.join(skill_App.config['UPLOAD_FOLDER'], filename))
                    else:
                        message = "يجب رفع ملف صورة"
                else:
                    message = "يجب رفع ملف صورة"

            # التحقق من صحة البيانات
            if not idnum.isnumeric():
                message = "الرقم الوظيفي يجب أن يحتوي على أرقام فقط"
            elif not is_valid_email(email):
                message = "البريد الإلكتروني غير صالح (يجب أن يكون @mbl.com.sa)"
            elif not is_valid_mobile(mobile):
                message = "رقم الهاتف غير صالح. يجب أن يكون بالشكل: [0512345678]"
            elif not is_valid_idnum(idnum):
                message = "الرقم الوظيفي غير صالح"
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # التحقق من وجود المستخدم بالبريد أو الرقم الوظيفي
                        cursor.execute("SELECT * FROM users WHERE idnum = %s", (idnum,))
                        if cursor.fetchone():
                            message = "رقم الموظف موجود بالفعل!"
                        else:
                            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                            if cursor.fetchone():
                                message = "البريد الإلكتروني موجود بالفعل!"
                            else:
                                cursor.execute("SELECT * FROM users WHERE mobile = %s", (mobile,))
                                if cursor.fetchone():
                                    message = "رقم الموبايل موجود بالفعل!"
                                else:
                                    hashed_password = hash_password(password)  # تشفير كلمة السر
                                    filename_Null= filename if filename else ""
                                    cursor.execute(
                                        "INSERT INTO users (Name, idnum, email, mobile, password, department, reid, date, image,password_hid) "
                                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)",
                                        (name, idnum, email, mobile, hashed_password, department, reid, date_today, filename_Null,password)
                                    )
                                    conn.commit()
                                    message = "تم تسجيل المستخدم بنجاح!"
                except Exception as e:
                    return f"حدث خطأ أثناء معالجة الطلب: {str(e)}", 500

        return render_template("add.html",
                               pagetitle="تــسجيل",
                               style="add",
                               page_head="fa-solid fa-user-plus",
                               allertmas=message,
                               script="script",
                               userName=RfNameAndLastName(user_name),
                               img=user_img,
                               reid=reid)
    else:
        return redirect(url_for('loginpage'))




@skill_App.route("/edit")
def edit():
    if 'user_name' in session:
      user_name = session['user_name']
      user_img  = session['user_img']
      reid  = session['reid']
      user_id = request.args.get('id')
      with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users Where id = %s",(user_id,))
            edit = cursor.fetchone()
      return render_template("edit.html", 
                           pagetitle="تعديل", 
                           style="edit",
                             page_head="fa-solid fa-pen-to-square",
                             userName=RfNameAndLastName(user_name),
                             img=user_img,
                             editdata=edit,reid=reid)

    else:
        return redirect(url_for('loginpage'))
    

    # صفحة إضافة مستخدم
@skill_App.route("/Deviceinfo")
def Deviceinfopage():
    message=None
    if 'user_name' in session:
        user_name = session['user_name']
        user_img = session['user_img']
        reid = session['reid']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices")
            devices = cursor.fetchall()
            
            # قائمة لتخزين البيانات المدمجة
            devices_with_users = []
            
            for device in devices:
                cursor.execute("SELECT Name FROM users WHERE idnum = %s", (device[2],))
                user_data = cursor.fetchone()  # توقع اسم مستخدم واحد فقط
                if user_data:
                    devices_with_users.append({
                        "device": device,
                        "user_name": user_data[0]
                    })
        message = "تم تسجيل الجهاز بنجاح!"
        return render_template("Deviceinfo.html",
                               pagetitle="تــسجيل",
                               style="Deviceinfo",
                               page_head="fa-solid fa-laptop",
                               userName=RfNameAndLastName(user_name),
                               img=user_img,
                               reid=reid,
                               devices_with_users=devices_with_users,
                               allertmas=message,)
    
    else:
        return redirect(url_for('loginpage'))


 
 
@skill_App.route("/Device", methods=['GET', 'POST'])
def Devicepage():
    if 'user_name' in session:
        user_name = session['user_name']
        user_img = session['user_img']
        reid  = session['reid']
        message = None  # رسالة النجاح أو الخطأ
        if request.method == 'POST':
            # الحصول على بيانات الفورم
            Devicelocation = request.form.get('Devicelocation')
            idnum = request.form.get('idnum')
            department = request.form.get('department')
            pc_prand = request.form.get('pc_prand')
            PC_name = request.form.get('PC_name')
            PC_serial = request.form.get('PC_serial')
            screan = request.form.get('screan')
            screan_prand = request.form.get('screan_prand')
            screan_serial = request.form.get('screan_serial')
            printer = request.form.get('printer')
            printer_serial = request.form.get('printer_serial')
            printer_prand = request.form.get('printer_prand')

            # التحقق من صحة البيانات
            if not idnum.isnumeric():
                message = "الرقم الوظيفي يجب أن يحتوي على أرقام فقط"
            elif not is_valid_idnum(idnum):
                message = "   ادخل الرقم الوظيفي بشكل صحيح"
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        # تحقق من الرقم التسلسلي للأجهزة
                        cursor.execute("SELECT * FROM devices WHERE PC_serial = %s", (PC_serial,))
                        if cursor.fetchone():
                            message = " رقم التسلسل للجهاز موجود"
                        else:
                            cursor.execute("SELECT * FROM devices WHERE screan_serial = %s", (screan_serial,))
                            if cursor.fetchone():
                                message = " رقم التسلسل للشاشة موجود"
                            else:
                               
                                    printer_serial_value = printer_serial if printer_serial else "no "
                                    screan_serial_value = screan_serial if screan_serial else "no "
                                    screan_prand_value = screan_prand if screan_prand else "no"
                                    printer_prand_value = printer_prand if printer_prand else "no"
                                
                                    # إدخال البيانات في جدول الأجهزة
                                    cursor.execute(
                                        """INSERT INTO devices (Devicelocation, idnum, department, pc_prand,PC_name, PC_serial, screan, screan_serial ,printer, printer_serial, date,screan_prand,printer_prand) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,%s)""",
                                        (Devicelocation, idnum, department, pc_prand, PC_name, PC_serial, screan ,screan_serial_value , printer ,printer_serial_value ,date_today , screan_prand_value,printer_prand_value)
                                    )
                                    conn.commit()
                                    return redirect(url_for('Deviceinfopage'))
                except Exception as e:
                    return f"An error occurred: {e}"

        return render_template("Device.html",
                               pagetitle="تــسجيل",
                               style="Device",
                               page_head="fa-solid fa-laptop",
                               allertmas=message,
                               script="script",
                               userName=RfNameAndLastName(user_name),
                               img=user_img,reid=reid)
    else:
        return redirect(url_for('loginpage'))

# register user 
@skill_App.route("/Register", methods=['GET', 'POST'])
def Register():
 
    message = None  # رسالة النجاح أو الخطأ
    if request.method == 'POST':

        # الحصول على بيانات الفورم
        name = request.form.get('name')
        idnum = request.form.get('idnum')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        department = request.form.get('department')
        reid ="2"
        img =""
      
       

        # التحقق من صحة البيانات
        if not idnum.isnumeric():
            message = "الرقم الوظيفي يجب أن يحتوي على أرقام فقط"
        elif not is_valid_email(email):
            message = "  البريد الإلكتروني غير صالح\n @mbl.com.sa"
        elif not is_valid_mobile(mobile):
            message = " [0512345678] ادخل الموبيل  بشكل  صحيح"
        elif not is_valid_idnum(idnum):
            message = "   ادخل الرقم  الوظفي  بشكل  صحيح"
        else:
            try:
                with get_db_connection() as conn:
                    # تحقق إذا كان البريد الإلكتروني أو الرقم الوظيفي موجودًا
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE idnum = %s", (idnum,))
                    existing_user = cursor.fetchone()
                    if existing_user:
                        message = "رقم الموظف موجود بالفعل!"
                    else:
                        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                        existing_email = cursor.fetchone()
                        if existing_email:
                            message = "البريد الإلكتروني موجود بالفعل!"
                        else:
                            hashed_password = hash_password(password)  # تشفير كلمة السر
                            cursor.execute("INSERT INTO users (Name, idnum, email,mobile, password, department, reid,date,image,password_hid) VALUES (%s,%s,%s, %s, %s, %s, %s, %s,%s,%s)",
                                           (name, 
                                            idnum, 
                                            email,
                                            mobile, 
                                            hashed_password, 
                                            department, 
                                            reid,
                                            date_today,
                                            img,password))
                            conn.commit()
                            return redirect(url_for('Registersucsspage'))
            except Exception as e:
              return f"An error occurred: {str(e)}"

    return render_template("Register.html",
                            pagetitle="Register",
                              style="Register", 
                              page_head="fa-solid fa-square-plus",
                              allertmas= message,
                                  script="script",
                                  sidebar='no')



@skill_App.route("/Registersucss",methods=['GET', 'POST'])
def Registersucsspage():
     message = "تم التسجيل بنجاح!"
     return render_template("Registersucss.html",
                            pagetitle="Registersucss",
                              style="Registersucss", 
                              script="script",
                              allertmas= message,
                              sidebar='no')


@skill_App.route("/Projects")
def Projectspage():
  if 'user_name' in session:
        user_name = session['user_name']
        user_img  = session['user_img']
        reid  = session['reid']
        try:
            # الاتصال بقاعدة البيانات
            with get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM projects")
                result = cursor.fetchall()
            return render_template("Projects.html",
                            pagetitle="Projects",
                              style="Projects", 
                                 userName=RfNameAndLastName(user_name),
                                 page_head="fa-solid fa-square-plus",
                                   img=user_img,
                                   reid=reid,result=result)
        except Exception as e:
            # معالجة الخطأ (يمكن تحسين عرض الخطأ)
            return f"حدث خطأ أثناء الاتصال بقاعدة البيانات: {str(e)}", 500
  else:
        return redirect(url_for('loginpage'))
  

@skill_App.route("/addprojects", methods=['GET', 'POST'])
def addprojectspage():
    if 'user_name' in session:
        # استرجاع بيانات المستخدم من الجلسة
        user_name = session['user_name']
        user_img = session['user_img']
        reid = session['reid']
        message = None  # رسالة النجاح أو الخطأ

        if request.method == 'POST':
            # الحصول على بيانات الفورم
            name = request.form.get('department')

            if not name:
                message = "الرجاء إدخال اسم المشروع."
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # التحقق إذا كان المشروع موجودًا مسبقًا
                        cursor.execute("SELECT * FROM projects WHERE Name = %s", (name,))
                        if cursor.fetchone():
                            message = "اسم المشروع موجود بالفعل!"
                        else:
                            # إدخال المشروع الجديد
                            cursor.execute("INSERT INTO projects (Name) VALUES (%s)", (name,))
                            conn.commit()
                            message = "تم إضافة المشروع بنجاح!"
                except Exception as e:
                    return f"حدث خطأ أثناء إضافة المشروع: {str(e)}", 500

        return render_template("addprojects.html",
                               pagetitle="Add Projects",
                               style="addprojects",
                               script="script",
                               userName=RfNameAndLastName(user_name),
                               img=user_img,
                               page_head="fa-solid fa-square-plus",
                               allertmas=message,
                               reid=reid)
    else:
        # إعادة التوجيه إلى صفحة تسجيل الدخول إذا لم يكن المستخدم مسجلاً
        return redirect(url_for('loginpage'))

@skill_App.route("/Settings", methods=['GET', 'POST'])
def Settingspage():
    if 'user_name' in session:
        # استرجاع بيانات المستخدم من الجلسة
        user_name = session['user_name']
        user_img = session['user_img']
        reid = session['reid']
        mobile_num = session['mobile_num']
        email = session['email']
        user_id = session['user_id']
        user_idnum = session['user_idnum']
        message = None  # رسالة النجاح أو الخطأ
        filename = None  # اسم الملف
        current_password_hid = None  # كلمة المرور المشفرة الحالية

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # جلب كلمة المرور المشفرة الحالية للمستخدم
                cursor.execute("SELECT password_hid FROM users WHERE idnum = %s", (user_idnum,))
                result = cursor.fetchone()
                current_password_hid = result[0] if result else None
        except Exception as e:
            return f"حدث خطأ أثناء جلب البيانات: {str(e)}", 500

        if request.method == 'POST':
            # استرجاع البيانات من الفورم
            name = request.form.get('name')
            mobile = request.form.get('mobile')
            password = request.form.get('password')

            # التحقق من الملف المرفوع
            file = request.files.get('file-upload')
            if file and file.filename:
                filename = secure_filename(file.filename)
                # التأكد من أن الملف صورة
                if filename.lower().endswith(('jpg', 'jpeg', 'png')):
                    # حفظ الصورة
                    file.save(os.path.join(skill_App.config['UPLOAD_FOLDER'], filename))
                else:
                    message = "الملف المرفوع يجب أن يكون صورة بصيغة (jpg, jpeg, png)."
                    filename = None
            elif not file:
                filename = None  # لا يوجد ملف مرفوع

            # التحقق من رقم الهاتف
            if not is_valid_mobile(mobile):
                message = "رقم الهاتف غير صالح. يجب أن يكون بالشكل: [0512345678]"
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # التحقق إذا كان رقم الهاتف موجودًا بالفعل
                        cursor.execute("SELECT * FROM users WHERE mobile = %s AND id != %s", (mobile, user_id))
                        if cursor.fetchone():
                            message = "رقم الهاتف موجود بالفعل لمستخدم آخر!"
                        else:
                            # تحديث بيانات المستخدم
                            hashed_password = hash_password(password)  # تشفير كلمة المرور
                            cursor.execute("""
                                UPDATE users 
                                SET name = %s, mobile = %s, password = %s, password_hid = %s, image = %s 
                                WHERE id = %s""", 
                                (name, mobile, hashed_password, password, filename or user_img, user_id))
                            conn.commit()
                            # تحديث الجلسة لتعكس التغييرات
                            session['user_name'] = name
                            session['mobile_num'] = mobile
                            session['user_img'] = filename or user_img
                            message = "تم تحديث بيانات المستخدم بنجاح."
                except Exception as e:
                    return f"حدث خطأ أثناء معالجة الطلب: {str(e)}", 500

        # عرض صفحة الإعدادات
        return render_template("Settings.html",
                               pagetitle="Settings",
                               style="Settings",
                               script="script",
                               userName=RfNameAndLastName(user_name),
                               fname=user_name,
                               img=user_img,
                               page_head="fa-solid fa-gear",
                               reid=reid,
                               mobile_num=mobile_num,
                               email=email,
                               current_password_hid=current_password_hid,
                               allertmas=message)
    else:
        # إعادة التوجيه إلى صفحة تسجيل الدخول إذا لم يكن المستخدم مسجلاً
        return redirect(url_for('loginpage'))




@skill_App.route("/logout")
def logout():
    session.clear()  # حذف بيانات الجلسة
    return redirect(url_for('loginpage'))


# تشغيل التطبيق
if __name__ == "__main__":
    skill_App.run(debug=True, port=90)
