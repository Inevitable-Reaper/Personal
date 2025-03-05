from tkinter import *
from PIL import Image, ImageTk
import customtkinter as ck
from tkinter import filedialog as fd        
import base64
import mysql.connector as myc
from datetime import datetime, timezone
import io
import numpy as np
from threading import Thread
import silence_tensorflow.auto
import time
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.applications import ResNet50V2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from keras import regularizers
from customtkinter import CTkImage


# Database connection
conn = myc.connect(host='localhost', user='root', password='Y1a2s3h4#', database='pnue')
cursor = conn.cursor()



model = None
model_loaded = False

# Function to create the model
def make_model():
    global model, model_loaded

    base_model = ResNet50V2(weights='imagenet', input_shape=(224, 224, 3), include_top=False)
    model = Sequential([
        Input(shape=(224, 224, 3)),  # Explicitly add an input layer
        base_model,
        GlobalAveragePooling2D(),
        Dense(512, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
        Dropout(0.5),
        Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
        Dropout(0.3),
        Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.load_weights("D:\Project Final\save_model\model_fine.weights.h5")
    model_loaded = True

# Start the thread for model loading
Thread(target=make_model, name="model_maker").start()

# Connect to the database
def connect():
    global cursor, conn
    conn = myc.connect(host='localhost', user='root', password='Y1a2s3h4#', database='pnue')
    cursor = conn.cursor()


# Verify the token
def verify(token):
    connect()
    q = "Select token_num from patient where token_num = " + str(token)
    cursor.execute(q)
    data = cursor.fetchall()
    conn.close()
    return not data

# Display function
def display(data):
    connect()
    n = []
    for row in data:
        d = []
        for i in row:
            d.append(i)
        n.append(d)
    conn.close()
    if len(n) == 1:
        return d
    else:
        return n

# Add patient data to the database
def add(name, token, date, loc, pred):
    q = "Insert into patient values(%s,%s,%s,%s,%s);"
    blob = img_to_bin(loc)
    values = (name, str(token), str(date), blob, pred)
    connect()
    cursor.execute(q, values)
    conn.commit()
    conn.close()

# Search data in the database
def searchindata(name='', token=0):
    q = "select * from patient where name=%s or token_num=%s"
    values = (name, str(token))
    connect()
    cursor.execute(q, values)
    data = display(cursor.fetchall())
    if isinstance(data[0], list):
        for i in range(len(data)):
            data[i][3] = bin_to_img(data[i][3])
        return data, "multiple"
    else:
        data[3] = bin_to_img(data[3])
        return data, "single"

# Prediction function
def predict(loc):
    while not model_loaded:
        print("waiting for model to load")
        time.sleep(1)
    else:
        img = Image.open(loc).resize((224, 224))
        if img.mode != "RGB":
            img = img.convert("RGB")
        x = np.asarray(img) / 255.0  # Normalize to [0, 1]
        x = np.expand_dims(x, axis=0)

        classes = model.predict(x)
        print(f"Prediction confidence: {classes[0]}")

        if classes[0] > 0.5:
            return "Pnuemonia"
        else:
            return "Normal"

# Convert image to binary
def img_to_bin(loc):
    try:
        with open(loc, "rb") as file:
            binary = file.read()
            binary = base64.b64encode(binary)
        return binary
    except Exception as e:
        print(f"Problem with image: {e}")

def bin_to_img(binary):
    try:
        binary = base64.b64decode(binary)
        image = io.BytesIO(binary)
        return image
    except Exception as e:
        print(f"Failed to create image: {e}")

ck.set_appearance_mode("dark")
ck.set_default_color_theme("blue")
loc = ""
bg_img = "D:\\Project Final\\images\\imageg-dark.ppm"
options = "Light"

# Save the PDF report
def pdfsave(frame, loc, name, date, token, pred):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=20, style="B")
    pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 10, txt="Chest X-ray", ln=1, align='C')
    pdf.cell(200, 10, txt="Report", ln=2, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", size=20, style="B")
    pdf.cell(200, 10, txt="Name of patient: " + name, ln=2, align="L")
    pdf.cell(200, 10, txt="Date of Diagnosis: " + date, ln=2, align="L")
    pdf.cell(200, 10, txt="Token Number: " + str(token), ln=2, align="L")
    pdf.cell(200, 10, txt="Prediction: " + pred, ln=2, align="L")
    pdf.image(loc, x=0, y=100, w=150, h=150)
    dest = fd.askdirectory(title="Select Folder to open")
    dest += "/" + name + "_" + str(token) + ".pdf"
    pdf.output(dest, "f")


def output(frame, img, name, date, token, pred, backloc):
    frame.destroy()
    frame = ck.CTkFrame(master=root, height=800, width=1280)
    frame.pack()

    bg_img_loaded = Image.open(bg_img)
    bg = CTkImage(light_image=bg_img_loaded, size=(1280, 800))
    background = ck.CTkLabel(master=frame, image=bg)
    background.pack()

    img_resized = img.resize((400, 400))
    x_ray = CTkImage(light_image=img_resized, size=(400, 400))
    picture = ck.CTkLabel(master=frame, image=x_ray)
    picture.place(relx=.5, rely=.5, x=-300, y=-100, anchor=CENTER)

    x = -100
    y = -100
    name_Label = ck.CTkLabel(master=frame, text="Name of patient")
    name_Label.place(relx=.5, rely=.5, anchor=CENTER, x=x, y=y)
    date_Label = ck.CTkLabel(master=frame, text="Date of diagnosis")
    date_Label.place(relx=.5, rely=.5, anchor=CENTER, x=x, y=y+70)
    token_Label = ck.CTkLabel(master=frame, text="Token Number")
    token_Label.place(relx=.5, rely=.5, anchor=CENTER, x=x, y=y+140)
    pred_Label = ck.CTkLabel(master=frame, text="Prediction")
    pred_Label.place(relx=.5, rely=.5, anchor=CENTER, x=x, y=y+210)

    name_info = ck.CTkLabel(master=frame, text=name)
    name_info.place(relx=.5, rely=.5, anchor=CENTER, x=x+200, y=y)
    date_info = ck.CTkLabel(master=frame, text=date)
    date_info.place(relx=.5, rely=.5, anchor=CENTER, x=x+200, y=y+70)
    token_info = ck.CTkLabel(master=frame, text=token)
    token_info.place(relx=.5, rely=.5, anchor=CENTER, x=x+200, y=y+140)
    pred_info = ck.CTkLabel(master=frame, text=pred)
    pred_info.place(relx=.5, rely=.5, anchor=CENTER, x=x+200, y=y+210)

    save = ck.CTkButton(master=frame, text="Save report", command=lambda: pdfsave(frame, loc, name, date, token, pred))
    save.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=250)
    back_button = ck.CTkButton(master=frame, text="Back", command=lambda: back(frame, backloc))
    back_button.place(relx=.5, rely=.5, anchor=CENTER, x=300, y=300)


def back(frame, backloc):
    frame.destroy()
    if backloc == "welcome":
        next = welcome()
        next.screen()
    elif backloc == "check":
        next = check()
        next.screen()

# Welcome screen class
class welcome():
    def screen(self):
        super()
        global bg_img, options
        self.frame = ck.CTkFrame(master=root, height=800, width=1280)
        self.frame.pack()


        bg_img_loaded = Image.open(bg_img)
        bg = CTkImage(light_image=bg_img_loaded, size=(1280, 800))
        self.background = ck.CTkLabel(master=self.frame, image=bg)
        self.background.pack()

        check = ck.CTkButton(master=self.frame, text="Check patient details", command=lambda: self.call_check())
        check.place(relx=.5, rely=.5, anchor=CENTER, x=-150, y=80)
        pred = ck.CTkButton(master=self.frame, text="Get prediction", command=lambda: self.call_Prediction())
        pred.place(relx=.5, rely=.5, anchor=CENTER, x=150, y=80)
        quit = ck.CTkButton(master=self.frame, text="Quit", command=lambda: exit())
        quit.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=150)
        optionmenu_1 = ck.CTkButton(master=self.frame, text=options + " Mode", command=self.change_appearance_mode)
        optionmenu_1.place(x=10, y=650)

    def change_appearance_mode(self):
        global bg_img, options, button_ico, button_color
        if options == "Light":
            bg_img = "D:\\Project Final\\images\\imageg-light.ppm"
            ck.set_appearance_mode(options)
            options = "Dark"
            ck.set_default_color_theme("green")
        elif options == "Dark":
            bg_img = "D:\\Project Final\\images\\imageg-dark.ppm"
            ck.set_appearance_mode(options)
            options = "Light"
            button_ico = bg_img
            button_color = "black"
            ck.set_default_color_theme("blue")

        self.frame.destroy()
        load = welcome()
        load.screen()

    def call_Prediction(self):
        self.frame.destroy()
        next = prediction()
        next.screen()

    def call_check(self):
        self.frame.destroy()
        next = check()
        next.screen()

class prediction():
    def screen(self):
        global bg_img
        self.frame = ck.CTkFrame(master=root, height=800, width=1280)
        self.frame.pack()

        # Load the background image using CTkImage
        bg_img_loaded = Image.open(bg_img)
        bg = CTkImage(light_image=bg_img_loaded, size=(1280, 800))
        background = ck.CTkLabel(master=self.frame, image=bg)
        background.pack()

        name_var = StringVar()
        entry_1 = ck.CTkEntry(master=self.frame, textvariable=name_var, width=400)
        entry_1.place(relx=.5, rely=.5, anchor=CENTER, x=80, y=0)
        name_label = ck.CTkLabel(master=self.frame, text="Name of patient")
        name_label.place(relx=.5, rely=.5, anchor=CENTER, x=-130, y=0)
        open_button = ck.CTkButton(master=self.frame, text="Upload x-ray", command=self.getfile)
        open_button.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=80)
        self.process = ck.CTkButton(master=self.frame, text="Proceed", command=lambda: self.proceed(name_var))
        self.process.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=140)
        self.process.configure(state=DISABLED)
        back_button = ck.CTkButton(master=self.frame, text="Back", command=self.back)
        back_button.place(relx=.5, rely=.5, anchor=CENTER, x=300, y=300)
        optionmenu_1 = ck.CTkButton(master=self.frame, text=options + " Mode", command=self.change_appearance_mode)
        optionmenu_1.place(x=10, y=650)

    def proceed(self, name_var):
        import random
        username = name_var.get()
        token = random.randint(0, 99999)
        if not verify(token):
            token = random.randint(0, 99999)
        date = datetime.now().strftime("%Y-%m-%d")
        img = Image.open(loc)
        try:
            pred = predict(loc)
            add(username, token, date, loc, pred)
            output(self.frame, img, username, date, token, pred, "welcome")
        except Exception as e:
            print(f"Error occurred: {e}")
            error_label = ck.CTkLabel(master=self.frame, text=f"Error Occurred: {str(e)}", text_color="red", font=("", 15))
            error_label.place(relx=.5, rely=.5, anchor=CENTER, x=-50, y=200)

    def back(self):
        self.frame.destroy()
        next = welcome()
        next.screen()

    def getfile(self):
        the_file = fd.askopenfilename(
            title="Select a file of any type",
            filetypes=[("jpg file", "*.jpeg*"), ("png file", "*.png*"), ("All file", "*.*")]
        )
        global loc
        loc = the_file
        img = Image.open(loc)

        img_resized = img.resize((300, 300))
        x_ray = CTkImage(light_image=img_resized, size=(300, 300))
        picture = ck.CTkLabel(master=self.frame, image=x_ray)
        picture.place(relx=0, rely=0, anchor=NW)
        self.process.configure(state=NORMAL)

    def change_appearance_mode(self):
        global bg_img, options, button_ico, button_color
        if options == "Light":
            bg_img = "D:\\Project Final\\images\\imageg-light.ppm"
            ck.set_appearance_mode(options)
            options = "Dark"
            ck.set_default_color_theme("green")
        elif options == "Dark":
            bg_img = "D:\\Project Final\\images\\imageg-dark.ppm"
            ck.set_appearance_mode(options)
            options = "Light"
            button_ico = bg_img
            button_color = "black"
            ck.set_default_color_theme("blue")
        self.frame.destroy()
        load = prediction()
        load.screen()

class check():
    def screen(self):
        global bg_img, options
        self.frame = ck.CTkFrame(master=root, height=800, width=1280)
        self.frame.pack()

        # Load the background image using CTkImage
        bg_img_loaded = Image.open(bg_img)
        bg = CTkImage(light_image=bg_img_loaded, size=(1280, 800))
        background = ck.CTkLabel(master=self.frame, image=bg)
        background.pack()

        option = ck.CTkLabel(master=self.frame, text="Enter details in one of the following and search")
        option.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=-70)

        name_var = StringVar()
        entry_1 = ck.CTkEntry(master=self.frame, textvariable=name_var, width=400)
        entry_1.place(relx=.5, rely=.5, anchor=CENTER, x=80, y=0)
        name_label = ck.CTkLabel(master=self.frame, text="Name of patient")
        name_label.place(relx=.5, rely=.5, anchor=CENTER, x=-130, y=0)

        token_var = StringVar()
        entry_2 = ck.CTkEntry(master=self.frame, textvariable=token_var, width=400)
        entry_2.place(relx=.5, rely=.5, anchor=CENTER, x=80, y=80)
        token_label = ck.CTkLabel(master=self.frame, text="Token number")
        token_label.place(relx=.5, rely=.5, anchor=CENTER, x=-130, y=80)

        search_it = ck.CTkButton(master=self.frame, text="Search", command=lambda: self.search(token_var, name_var))
        search_it.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=150)

        back_button = ck.CTkButton(master=self.frame, text="Back", command=self.back)
        back_button.place(relx=.5, rely=.5, anchor=CENTER, x=300, y=300)
        optionmenu_1 = ck.CTkButton(master=self.frame, text=options + " Mode", command=self.change_appearance_mode)
        optionmenu_1.place(x=10, y=650)

    def back(self):
        self.frame.destroy()
        next = welcome()
        next.screen()

    def search(self, token_var, name_var):
        name = name_var.get()
        token = token_var.get()
        data, decide = searchindata(name, token)
        if data:
            if decide == "single":
                image = Image.open(data[3])
                output(self.frame, image, data[0], data[2], data[1], data[4], "check")
            if decide == "multiple":
                self.multiple_options(data)
        else:
            warning = ck.CTkLabel(master=self.frame, text="No Data found", text_color="red", font=("", 15))
            warning.place(relx=.5, rely=.5, anchor=CENTER, x=-50, y=200)

    def send_to_output(self, data):
        image = Image.open(data[3])
        output(self.frame, image, data[0], data[1], data[2], data[4], "check")

    def multiple_options(self, data):
        self.frame.destroy()
        v = StringVar(self.frame, "0")
        global bg_img
        self.frame = ck.CTkFrame(master=root, height=800, width=1280)
        self.frame.pack()

        bg_img_loaded = Image.open(bg_img)
        bg = CTkImage(light_image=bg_img_loaded, size=(1280, 800))
        background = ck.CTkLabel(master=self.frame, image=bg)
        background.pack()

        values = {}
        for i in data:
            key = i[0] + " " + str(i[1]) + " " + str(i[2])
            values[key] = data.index(i)
        x = 0
        y = -120
        for text, value in values.items():
            ck.CTkRadioButton(master=self.frame, text=text, variable=v, value=value).place(relx=.5, rely=.5, anchor=CENTER, x=x, y=y)
            y += 40

        proceed = ck.CTkButton(master=self.frame, text="Select", command=lambda: self.proceed(v, data))
        proceed.place(relx=.5, rely=.5, anchor=CENTER, x=0, y=300)

    def proceed(self, v, data):
        index = int(v.get())
        send = data[index]
        self.send_to_output(send)

    def change_appearance_mode(self):
        global bg_img, options
        if options == "Light":
            bg_img = "D:\\Project Final\\images\\imageg-light.ppm"
            ck.set_appearance_mode(options)
            options = "Dark"
            ck.set_default_color_theme("green")
        elif options == "Dark":
            bg_img = "D:\\Project Final\\images\\imageg-dark.ppm"
            ck.set_appearance_mode(options)
            options = "Light"
            ck.set_default_color_theme("blue")
        self.frame.destroy()
        load = check()
        load.screen()

# Main
root = ck.CTk()
root.geometry("1600x900+160+90")
root.title('Pneumonia Detection')
root.resizable(False, False)
w = welcome()
w.screen()
root.mainloop()
