import RPi.GPIO as GPIO
import time
import dash
from dash.dependencies import Input, Output
import dash_daq as daq
from dash import dcc
from dash import html
import random
from paho.mqtt import client as mqtt_client
from datetime import date
import smtplib
import email
import imaplib
import sys
import glob
import dash_bootstrap_components as dbc
import os
import pygame
# Random variables that work for some reason
external_scripts = ["/assets/jquery.min.js"]

#external_stylesheets = ["assets/header.css"]


app = dash.Dash(
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = "IOT DashBoard"
#app.scripts.config.serve_locally=True
app.css.config.serve_locally = True

app.config["suppress_callback_exceptions"]=True
pin = 17
broker = '10.0.0.103'
port = 1883
topic = [("IoTLab/light",0),("IoTLab/temp",0),("IoTLab/humi",0),("IoTLab/rfid",0)]
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
username = 'Dharmin'
password = '1234'
LED_PIN = 6
isOn = "Light is off"
isOnMotor = False
motorMsg = "Motor is off"
tempMsg = ""
humiMsg = ""
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
lightVal = 0
state = 5
message = ""
messageMotor = ""
sentMotorMail = False
sentEmailCount = 0
in1 = 18
in2 = 23
in3 = 25
in4 = 22
users = ['','1474525640', '313552731']
prefTemp = ['',20 , 25]
prefHumi = ['',50, 60]
prefLight = ['',400,1500]
profiles = ['','https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fwww.spshabitat.org%2Fwp-content%2Fuploads%2F2020%2F01%2F74046195_s-300x300.jpg&f=1&nofb=1',
            'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fronaldmottram.co.nz%2Fwp-content%2Fuploads%2F2019%2F01%2Fdefault-user-icon-8-300x300.jpg&f=1&nofb=1']
userPosition = 0
uidMessage = "Please Scan Your RFID to Start the Guages"
app.config["suppress_callback_exceptions"]=True
# careful lowering this, at some point you run into the mechanical limitation of how quick your motor can move
step_sleep = 0.002
 
step_count = 40960 # 5.625*(1/64) per step, 4096 steps is 360°
 
direction = False # True for clockwise, False for counter-clockwise
 
# defining stepper motor sequence (found in documentation http://www.4tronix.co.uk/arduino/Stepper-Motors.php)
step_sequence = [[1,0,0,1],
                 [1,0,0,0],
                 [1,1,0,0],
                 [0,1,0,0],
                 [0,1,1,0],
                 [0,0,1,0],
                 [0,0,1,1],
                 [0,0,0,1]]
 
# setting up
GPIO.setmode( GPIO.BCM )
GPIO.setup( in1, GPIO.OUT )
GPIO.setup( in2, GPIO.OUT )
GPIO.setup( in3, GPIO.OUT )
GPIO.setup( in4, GPIO.OUT )
 
# initializing
GPIO.output( in1, GPIO.LOW )
GPIO.output( in2, GPIO.LOW )
GPIO.output( in3, GPIO.LOW )
GPIO.output( in4, GPIO.LOW )
 
 
motor_pins = [in1,in2,in3,in4]
motor_step_counter = 0 ;

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

lightOnPath="/home/pi/Downloads/SoundInOggFormat/LightOn.ogg"
lightOffPath="/home/pi/Downloads/SoundInOggFormat/LightOff.ogg"
fanOnPath="/home/pi/Downloads/SoundInOggFormat/FanOn.ogg"
fanOffPath="/home/pi/Downloads/SoundInOggFormat/FanOff.ogg"
humidityHighPath="/home/pi/Downloads/SoundInOggFormat/HumidityHigh.ogg"
humidityLowPath="/home/pi/Downloads/SoundInOggFormat/HumidityLow.ogg"
welcomeMsgPath="/home/pi/Downloads/SoundInOggFormat/Welcome.ogg"
newMailPath="/home/pi/Downloads/SoundInOggFormat/NewEmailNotif.ogg"

def Layout(): 
    app.layout = html.Div([
        dbc.Nav([
                dbc.NavLink("Guages", href="/", id="page-1-link"),
                dbc.NavLink("User profile", href="/page-2", id="page-2-link"),
            ], vertical=True, pills=True,style=SIDEBAR_STYLE),
        dcc.Location(id="url",refresh=False),
        html.Div(id='page-content',style=CONTENT_STYLE),
        dcc.Interval(id="rfid_interval",
        interval=1*5000,
        n_intervals=0),
    ])
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global lightMsg
        global humiMsg
        global sentMotorMail
        global tempMsg
        global sentEmailCount
        global state
        global message
        global lightVal
        global isOn
        global uidNumber
        global uidMessage
        global users
        global userPosition
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        message = ""
        messageMotor = ""
        if (msg.topic == 'IoTLab/rfid'):
            audio_player(welcomeMsgPath)
            uidMessage = "User UID: ", msg.payload.decode()
            userPosition = users.index(msg.payload.decode())
            sendUIDMail(uidMessage)
        elif (uidMessage != "Please Scan Your RFID to Start the Guages"):
            if (msg.topic == 'IoTLab/light'):
                lightMsg = int(msg.payload.decode())
                print(lightMsg)
            elif (msg.topic == 'IoTLab/humi'):
                humiMsg = float(msg.payload.decode())
            elif (msg.topic == 'IoTLab/temp'):
                tempMsg = float(msg.payload.decode())
                if (tempMsg > prefTemp[userPosition] and sentMotorMail != True and sentEmailCount == 0):
                    sendMotorEmail()
                    messageMotor = "Email was sent to Turn on motor"
                    audio_player(newMailPath)
                    sentEmailCount += 1
                    sentMotorMail = True
            if (sentMotorMail == True and sentEmailCount == 1):
                reply = receiveEmail()
                #print('is spinning')
            if (state != 0 and lightMsg < prefLight[userPosition]):
                state = 0
                isOn = "Light is On"
                message = "Email was sent when light was turned on"
                audio_player(lightOnPath)
                lightVal = lightMsg
                GPIO.output(LED_PIN, GPIO.HIGH)
                sendEmail()
            elif (lightMsg > prefLight[userPosition]):
                state = 1
                message = ""
                audio_player(lightOffPath)
                isOn = "Light is off"
                lightVal = lightMsg
                GPIO.output(LED_PIN, GPIO.LOW)
    client.subscribe(topic)
    client.on_message = on_message


# def run():
#     client = connect_mqtt()
#     subscribe(client)
#     client.loop_forever()      
def sendEmail():
    with smtplib.SMTP('smtp.gmail.com',587) as smtp :
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login('dharminp721@gmail.com','Python1234')
        now = date.today()
        d1 = now.strftime("%d/%m/%Y")
        subject = 'Subject'
        body = 'Light was turned on at ', d1

        msg = f'Subject: {subject}\n\n{body}'

        smtp.sendmail('dharminp721@gmail.com', 'dharminp721@gmail.com', msg)
        
def sendMotorEmail():
    with smtplib.SMTP('smtp.gmail.com',587) as smtp :
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login('dharminp721@gmail.com','Python1234')
        now = date.today()
        d1 = now.strftime("%d/%m/%Y")
        subject = 'Motor'
        body = 'Would you like to turn on the fan?'

        msg = f'Subject: {subject}\n\n{body}'

        smtp.sendmail('dharminp721@gmail.com', 'dharminp721@gmail.com', msg)
        
def sendUIDMail(uid):
    with smtplib.SMTP('smtp.gmail.com',587) as smtp :
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login('dharminp721@gmail.com','Python1234')
        now = date.today()
        d1 = now.strftime("%d/%m/%Y")
        subject = 'User', uid , 'Logged in'
        body = 'UID'

        msg = f'Subject: {subject}\n\n{body}'

        smtp.sendmail('dharminp721@gmail.com', 'dharminp721@gmail.com', msg)    
        
def getSensorData():
    dht.readDHT11()
    return dht.temperature,dht.humidity

@app.callback(Output('temperature', 'value'),
                  Output('humidity', 'value'),
                  Output('light', 'value'),
                  Output('message', 'children'),
                  Output('isOn', 'children'),
                  Output('isOnMotor', 'children'),
                  Output('uidMessage', 'children'),
                  Input('interval-component', 'n_intervals'))
def update_gauges(n):
        return tempMsg,humiMsg,lightMsg,message,isOn,motorMsg,uidMessage
          
def spinMotor():
    global motorMsg
    global motor_pins
    global step_count
    global step_sequence
    global motor_step_counter
    motorMsg = "Motor is on"
    step_sleep = 0.002
    try:
        i = 0
        for i in range(step_count):
            for pin in range(0, len(motor_pins)):
                GPIO.output( motor_pins[pin], step_sequence[motor_step_counter][pin] )
            if direction==True:
                motor_step_counter = (motor_step_counter - 1) % 8
            elif direction==False:
                motor_step_counter = (motor_step_counter + 1) % 8
            else: # defensive programming
                print( "uh oh... direction should *always* be either True or False" )
                cleanup()
                exit( 1 )
            time.sleep( step_sleep )
    except KeyboardInterrupt:
        exit( 1 )
    spinMotor()
def receiveEmail():
    EMAIL = 'dharminp721@gmail.com'
    PASSWORD = 'Python1234'
    SERVER = 'imap.gmail.com'
    global sentEmailCount
    global isOnMotor
    # connect to the server and go to its inbox
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    # we choose the inbox but you can select others
    mail.select('inbox')

    # we'll search using the ALL criteria to retrieve
    # every message inside the inbox
    # it will return with its status and a list of ids
    status, data = mail.search(None, 'FROM dharminp721@gmail.com SUBJECT Motor UNSEEN')
    # the list returned is a list of bytes separated
    # by white spaces on this format: [b'1 2 3', b'4 5 6']
    # so, to separate it first we create an empty list
    mail_ids = []
    # then we go through the list splitting its blocks
    # of bytes and appending to the mail_ids list
    for block in data:
        # the split function called without parameter
        # transforms the text or bytes into a list using
        # as separator the white spaces:
        # b'1 2 3'.split() => [b'1', b'2', b'3']
        mail_ids += block.split()

    # now for every id we'll fetch the email
    # to extract its content
    for i in mail_ids:
        # the fetch function fetch the email given its id
        # and format that you want the message to be
        status, data = mail.fetch(i, '(RFC822)')
        # the content data at the '(RFC822)' format comes on
        # a list with a tuple with header, content, and the closing
        # byte b')'
        for response_part in data:
            # so if its a tuple...
            if isinstance(response_part, tuple):
                # we go for the content at its second element
                # skipping the header at the first and the closing
                # at the third
                message = email.message_from_bytes(response_part[1])

                # with the content we can extract the info about
                # who sent the message and its subject
                mail_from = message['from']
                mail_subject = message['subject']

                # then for the text we have a little more work to do
                # because it can be in plain text or multipart
                # if its not plain text we need to separate the message
                # from its annexes to get the text
                if message.is_multipart():
                    mail_content = ''

                    # on multipart we have the text message and
                    # another things like annex, and html version
                    # of the message, in that case we loop through
                    # the email payload
                    for part in message.get_payload():
                        # if the content type is text/plain
                        # we extract it
                        if part.get_content_type() == 'text/plain':
                            mail_content = part.get_payload()
                            reply = f'Content: {mail_content}'
                            if ("YES" in reply):
                                sentEmailCount += 1
                                spinMotor()
                                isOnMotor = True
                                return isOnMotor
                else:
                    # if the message isn't multipart, just extract it
                    mail_content = message.get_payload()
                    return False

                # and then let's show its result
                #print(f'From: {mail_from}')
            #print(f'Subject: {mail_subject}')
            #print(f'Content: {mail_content}')

Layout()
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    global uidMessage
    prefLightMsg = "Preferred Light: ", prefLight[userPosition]
    prefHumiMsg = "Preferred Humidity: ", prefHumi[userPosition]
    prefTempMsg = "Preferred Temperature: ", prefTemp[userPosition]
    if (pathname == '/'):
        return html.Div([
                    html.Div(
            className="markdown-text",
            children=dcc.Markdown(
                children=(
                    """
            ###### What is this app about?
            Real time IOT Dashboard that sends out data and receive response regarding
            temperature, humidity, and light signal to decide whether or not to turn on
            the light or fan. 
        """
                )
            ),
        ),
        html.H1(children=message, id = "message",style={'text-align':'center'}),
        html.H1(children=message, id = "messageMotor",style={'text-align':'center'}),
                daq.Gauge(
            id='temperature',
            value=0,
            label='Temperature',
            units="Celsius",
            max=100,
            min=-20,
            color={"gradient":True,"ranges":{"blue":[-20, 10],"green":[10,60],"yellow":[60,80],"red":[80,100]}},
            style={'margin-right': '70%', 'display': 'block'},
            showCurrentValue = True,
        ),

        daq.Gauge(
            id='humidity',
            color={"gradient":True,"ranges":{"aqua":[0,30],"teal":[30,60],"blue":[60,80], "navy":[80,100]}},
            label="Humidity",
            value=0,
            units="Percentage",
            max=100,
            min=0,
            style={'margin-right': '70%', 'display': 'block','margin-bottom': '-50%'},
            showCurrentValue = True,
        ),
        html.Img(src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fcdn.iconscout.com%2Ficon%2Ffree%2Fpng-256%2Fbulb-idea-imagination-light-lamp-innovation-invention-6958.png&f=1&nofb=1"
            ,style={'margin-left':'auto','margin-right':'auto', 'display': 'block','margin-top':'300px'}),
        daq.LEDDisplay(
            id='light',
            label="Light Value ",
            value=10,
            style={'postion': '-40%', 'display': 'block'}
        ),
        dcc.Interval(id="interval-component",
            interval=1*10000,
            n_intervals=0),
        dcc.Interval(id="interval-motor",
            interval=1*20000,
            n_intervals=0),
        html.H1(children=isOn, id = "isOn",style={'text-align':'center'}),
        html.Img(src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fd1nhio0ox7pgb.cloudfront.net%2F_img%2Fo_collection_png%2Fgreen_dark_grey%2F256x256%2Fplain%2Ffan.png&f=1&nofb=1",style={'margin-left':'auto','margin-right':'auto', 'display': 'block'}),
        html.H1(children=motorMsg, id = "isOnMotor",style={'text-align':'center'}),
        html.H1(children=uidMessage, id = "uidMessage",style={'text-align':'center'}),
        ])
    if (pathname == '/page-2' and userPosition != 0):
        return html.Div([
        html.Img(src=profiles[userPosition],style={'margin-left':'auto','margin-right':'auto', 'display': 'block'}),
        html.H3(children= prefLightMsg, style={'text-align':'center'}),
        html.H3(children= prefHumiMsg, style={'text-align':'center'}),
        html.H3(children= prefTempMsg, style={'text-align':'center'})
    ])
    else:
        return html.H1(children="Please Scan RFID to see User profile", style={'text-align':'center'})
    
def playSound(filePath):
    pygame.mixer.music.load(filePath)
    pygame.mixer.music.play()

def audio_player(filePath):
    pygame.init()
    pygame.mixer.init()
    playSound(filePath)
    while pygame.mixer.music.get_busy() == True:
        continue
    return    
        
if __name__ == '__main__':
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
    app.run_server(debug=True)


