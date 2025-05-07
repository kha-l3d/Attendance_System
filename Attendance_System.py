import face_recognition
import cv2
import os
import numpy as np
import datetime
import csv
import tkinter as tk
from tkinter import ttk, messagebox

#  النافذة الرئيسية
root = tk.Tk()
root.title("Attendance System")
root.geometry("600x500")
root.configure(bg="#E6F0FA")

# Path 
image_folder = r"E:\matrial\CV\New folder\images_folder"
known_encodings = []
known_names = []

# Load  users
if os.path.exists(image_folder):
    for file_name in os.listdir(image_folder):
        if file_name.endswith((".jpg", ".png")):
            image_path = os.path.join(image_folder, file_name)
            print(f"Processing image: {image_path}")
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                name = os.path.splitext(file_name)[0].split("_")[0].lower()
                known_names.append(name)
                print(f"Successfully loaded face for user: {name}")
            else:
                print(f"No face detected in image: {image_path}")

# متغيرات عالمية
cap = None
camera_active = False
current_user = None
login_window_open = False
monitor_active = False

#  لتحقق لو اليوزر سجل النهارده
def has_user_attended_today(username):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists("attendance.csv"):
        return False
    
    with open("attendance.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2 and row[0].lower() == username.lower():
                try:
                    record_date = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                    if record_date == today:
                        return True
                except ValueError:
                    continue
    return False

#فضي النافذه   
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

#  لفتح الكاميرا
def start_camera():
    global cap, camera_active
    if not camera_active:
        cap = cv2.VideoCapture(0)
        if cap is None or not cap.isOpened():
            camera_active = False
            messagebox.showerror("Error", "Failed to open camera!")
            return False
        camera_active = True
        print("Camera opened successfully.")
        return True
    return True

#  لإغلاق الكاميرا
def stop_camera():
    global cap, camera_active, login_window_open, monitor_active
    if camera_active and cap is not None:
        cap.release()
        if login_window_open:
            try:
                cv2.destroyWindow("Verify Face - Press 'Esc' to Cancel")
            except cv2.error:
                pass
            login_window_open = False
        if monitor_active:
            try:
                cv2.destroyWindow("Team Monitor - Press 'Esc' to Exit")
            except cv2.error:
                pass
            monitor_active = False
        cv2.destroyAllWindows()
        camera_active = False
        print("Camera closed successfully.")

# الشاشة الرئيسية
def main_screen():
    clear_window()
    global current_user
    current_user = None
    stop_camera()
    root.configure(bg="#E6F0FA")
    
    tk.Label(root, text="Attendance System", font=("Arial", 18, "bold"), bg="#E6F0FA", fg="#333").pack(pady=20)
    
    tk.Button(root, text="Login", font=("Arial", 14), bg="#4CAF50", fg="white", width=20, command=login_screen).pack(pady=15)
    tk.Button(root, text="Register New User", font=("Arial", 14), bg="#2196F3", fg="white", width=20, command=register_screen).pack(pady=15)
    tk.Button(root, text="Exit", font=("Arial", 14), bg="#F44336", fg="white", width=20, command=root.quit).pack(pady=15)

# شاشة login
def login_screen():
    clear_window()
    root.configure(bg="#E6F0FA")
    
    tk.Label(root, text="Enter Username:", font=("Arial", 14), bg="#E6F0FA", fg="#333").pack(pady=20)
    username_entry = tk.Entry(root, font=("Arial", 12), width=25)
    username_entry.pack(pady=10)
    status_label = tk.Label(root, text="", font=("Arial", 12), bg="#E6F0FA", fg="#333")
    status_label.pack(pady=10)

    def verify_face():
        global current_user, login_window_open
        if not start_camera():
            status_label.config(text="Camera is not active!", fg="red")
            return

        username = username_entry.get().strip().lower()
        if not username:
            status_label.config(text="Please enter a username!", fg="red")
            return
        if username not in known_names:
            status_label.config(text="Username not found! Register first.", fg="red")
            return

        status_label.config(text="جاري التعرف...", fg="blue")
        login_window_open = True

        login_successful = False
        while camera_active:
            ret, frame = cap.read()
            if not ret:
                status_label.config(text="Failed to capture frame!", fg="red")
                stop_camera()
                return

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_detected = False
            face_encoding = None
            for (top, right, bottom, left) in face_locations:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                if face_encodings:
                    face_detected = True
                    face_encoding = face_encodings[0]

            if face_detected and face_encoding is not None:
                user_index = known_names.index(username)
                matches = face_recognition.compare_faces([known_encodings[user_index]], face_encoding)
                face_distances = face_recognition.face_distance([known_encodings[user_index]], face_encoding)
                if matches[0] and face_distances[0] < 0.5:
                    status_label.config(text="Login successful!", fg="green")
                    current_user = username
                    login_successful = True
                    break
                else:
                    status_label.config(text="Face does not match username!", fg="red")

            cv2.imshow("Verify Face - Press 'Esc' to Cancel", frame)
            key = cv2.waitKey(30) & 0xFF
            if key == 27:
                status_label.config(text="Login cancelled.", fg="red")
                stop_camera()
                return

        stop_camera()
        login_window_open = False

        if login_successful:
            after_login_screen()
        else:
            status_label.config(text="No face detected!", fg="red")

    tk.Button(root, text="Verify Face", font=("Arial", 12), bg="#4CAF50", fg="white", width=15, command=verify_face).pack(pady=10)
    tk.Button(root, text="Home", font=("Arial", 12), bg="#2196F3", fg="white", width=15, command=main_screen).pack(pady=10)

# شاشة بعد تسجيل الدخول
def after_login_screen():
    clear_window()
    root.configure(bg="#E6F0FA")
    
    tk.Label(root, text=f"Welcome, {current_user}!", font=("Arial", 16), bg="#E6F0FA", fg="#333").pack(pady=20)
    
    if not has_user_attended_today(current_user):
        tk.Button(root, text="Record Attendance", font=("Arial", 14), bg="#4CAF50", fg="white", width=20,
                 command=record_attendance).pack(pady=15)
    else:
        tk.Label(root, text="You have already attended today", font=("Arial", 12), bg="#E6F0FA", fg="#333").pack(pady=15)
    
    # إضافة زر Team Monitor فقط في شاشة ما بعد تسجيل الدخول
    tk.Button(root, text="Team Monitor", font=("Arial", 14), bg="#FF9800", fg="white", width=20,
             command=team_monitor_screen).pack(pady=15)
    tk.Button(root, text="Logout", font=("Arial", 14), bg="#F44336", fg="white", width=20,
             command=main_screen).pack(pady=15)

#  لتسجيل الحضور
def record_attendance():
    global current_user
    if current_user and not has_user_attended_today(current_user):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("attendance.csv", "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_user, current_time, "Present"])
        after_login_screen()

# شاشة تسجيل مستخدم جديد
def register_screen():
    clear_window()
    root.configure(bg="#E6F0FA")

    tk.Label(root, text="Enter Username:", font=("Arial", 14), bg="#E6F0FA", fg="#333").pack(pady=20)
    username_entry = tk.Entry(root, font=("Arial", 12), width=25)
    username_entry.pack(pady=10)
    status_label = tk.Label(root, text="", font=("Arial", 12), bg="#E6F0FA", fg="#333")
    status_label.pack(pady=10)

    def open_camera_for_registration():
        if not start_camera():
            status_label.config(text="Camera is not active!", fg="red")
            return

        username = username_entry.get().strip().lower()
        if not username:
            status_label.config(text="Please enter a username!", fg="red")
            return
        if username in known_names:
            status_label.config(text="Username already exists!", fg="red")
            return

        while camera_active:
            ret, frame = cap.read()
            if not ret:
                status_label.config(text="Camera error!", fg="red")
                break

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)

            for (top, right, bottom, left) in face_locations:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            cv2.imshow("Capture Your Face - Press 'c' to Capture", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                image_path = os.path.join(image_folder, f"{username}.jpg")
                cv2.imwrite(image_path, frame)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    # التحقق من تطابق الوجه مع الوجوه الموجودة
                    matches = face_recognition.compare_faces(known_encodings, encodings[0])
                    face_distances = face_recognition.face_distance(known_encodings, encodings[0])
                    if len(face_distances) > 0 and min(face_distances) < 0.5:
                        # إذا تم العثور على تطابق، رفض التسجيل
                        os.remove(image_path)
                        status_label.config(text="This face is already registered under another username!", fg="red")
                        break
                    else:
                        # إذا لم يكن هناك تطابق، متابعة التسجيل
                        known_encodings.append(encodings[0])
                        known_names.append(username)
                        status_label.config(text="Registered successfully!", fg="green")
                        break
                else:
                    status_label.config(text="No face detected in the image!", fg="red")
                    os.remove(image_path)
                    break
            elif key == 27:
                break

        cv2.destroyWindow("Capture Your Face - Press 'c' to Capture")
        stop_camera()

    tk.Button(root, text="Capture and Register", font=("Arial", 12), bg="#4CAF50", fg="white", width=20, command=open_camera_for_registration).pack(pady=20)
    tk.Button(root, text="Home", font=("Arial", 12), bg="#2196F3", fg="white", width=15, command=main_screen).pack(pady=10)


# شاشة Team  Monitor (ستظهر فقط بعد تسجيل الدخول)

def team_monitor_screen():
    clear_window()
    stop_camera()
    root.configure(bg="#E6F0FA")
    
    # فريم العرض 
    main_frame = tk.Frame(root, bg="#E6F0FA")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # عنوان الشاشة
    tk.Label(main_frame, text="Team Attendance Monitor", font=("Arial", 16, "bold"), bg="#E6F0FA", fg="#333").pack(pady=10)
    
    #  لعرض البيانات
    tree = ttk.Treeview(main_frame, columns=("Name", "Status", "Time"), show="headings")
    tree.heading("Name", text="Member")
    tree.heading("Status", text="Status")
    tree.heading("Time", text="Time")
    
    tree.column("Name", width=150, anchor="w")
    tree.column("Status", width=100, anchor="center")
    tree.column("Time", width=150, anchor="center")
    
    tree.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # إطار للأزرار السفلية
    button_frame = tk.Frame(main_frame, bg="#E6F0FA")
    button_frame.pack(pady=10)
    
    # camera wep
    def recognize_faces():
        global monitor_active
        if not start_camera():
            messagebox.showerror("Error", "Failed to open camera!")
            return
        
        monitor_active = True
        
        def update_recognition():
            if not monitor_active:
                return
            
            ret, frame = cap.read()
            if not ret:
                return
            
            # تغيير حجم الإطار لمعالجة أسرع
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # اكتشاف مواقع الوجوه
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
                # مقارنة الوجه مع الوجوه المعروفة
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                name = "Unknown"
                
                # استخدام أقرب وجه للمقارنة
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]
                
                # رسم المربع حول الوجه وكتابة الاسم
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow("Team Monitor - Press 'Esc' to Exit", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # زر Escape
                stop_monitoring()
            
            # جدولة التحديث التالي
            root.after(10, update_recognition)
        
        def stop_monitoring():
            global monitor_active
            monitor_active = False
            stop_camera()
            cv2.destroyAllWindows()
        
        # بدء التعرف
        update_recognition()
    
    #  لتحديث قائمة الحضور
    def update_attendance_list():
        # مسح البيانات القديمة
        for item in tree.get_children():
            tree.delete(item)
        
        # قراءة سجلات الحضور
        attendance_data = {}
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists("attendance.csv"):
            with open("attendance.csv", "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 2:
                        username = row[0]
                        try:
                            record_date = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                            if record_date == today:
                                attendance_data[username] = row[1]
                        except ValueError:
                            continue
        
        # عرض جميع المستخدمين مع حالة الحضور
        for name in sorted(known_names):
            if name in attendance_data:
                status = "Present"
                color = "green"
                time_str = attendance_data[name]
            else:
                status = "Absent"
                color = "red"
                time_str = "-"
            
            tree.insert("", "end", values=(name, status, time_str), tags=(color,))
        
        tree.tag_configure("green", foreground="green")
        tree.tag_configure("red", foreground="red")
    
    # تحديث القائمة أول مرة
    update_attendance_list()
    
    # زر للتعرف على الوجوه
    tk.Button(button_frame, text="Recognize Faces", font=("Arial", 12), bg="#FF9800", fg="white", width=15,
             command=recognize_faces).pack(side=tk.LEFT, padx=5)
    
    # زر للتحديث
    tk.Button(button_frame, text="Refresh List", font=("Arial", 12), bg="#2196F3", fg="white", width=15,
             command=update_attendance_list).pack(side=tk.LEFT, padx=5)
    
    # زر للعودة
    tk.Button(button_frame, text="Back", font=("Arial", 12), bg="#F44336", fg="white", width=15,
             command=after_login_screen).pack(side=tk.LEFT, padx=5)
# بدء البرنامج
if __name__ == "__main__":
    # إنشاء ملف الحضور إذا لم يكن موجوداً
    if not os.path.exists("attendance.csv"):
        with open("attendance.csv", "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Time", "Status"])
    
    # إنشاء مجلد الصور إذا لم يكن موجوداً
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    
    main_screen()
    root.mainloop()