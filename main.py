import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
import os
import json
import struct

FORMAT = "%(levelname)s:%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

app = FastAPI(title="Virtual Sense")

class HeaderPayloadDto(BaseModel):
    deviceId : str
    userId : str
    sessionStartTime : str
    frequency : str

class ReceiveDataPayloadDto(BaseModel):
    deviceId : str
    payload : list[int]

class EndSessionPayloadDto(BaseModel):
    deviceId : str
    sessionEndTime : str

class UserDetailsDto(BaseModel):
    username : str = Field(title="Please enter username")
    password : str = Field(title="Please enter password")
    displayName: str = Field(default= "", title="Please enter displayName")
    age: int = Field(default= 10, title="Please enter age")
    gender: str = Field(default= "", title="Please enter gender")
    userEmail: str = Field(default= "", title="Please enter userEmail")
    contactInformation: str = Field(default= "", title="Please enter contactInformation")
    medicalConditions: str = Field(default= "", title="Please enter medicalConditions")
    medications: str = Field(default= "", title="Please enter medications")
    fitnessGoals: str = Field(default= "", title="Please enter fitnessGoals")
    fitnessPlan: str = Field(default= "", title="Please enter fitnessPlan")
    chronicHealthConditions: str = Field(default= "", title="Please enter chronicHealthConditions")
    medicationHistory: str = Field(default= "", title="Please enter medicationHistory")
    dietaryHabits: str = Field(default= "", title="Please enter dietaryHabits")
    sleepQuality: str = Field(default= "", title="Please enter sleepQuality")
    notesComments: str = Field(default= "", title="Please enter notesComments")

class LoginDetailsDto(BaseModel):
    username : str
    password : str
    


def createDirectory(parent_dir,directory):
    path = os.path.join(parent_dir, directory)
    os.makedirs(path)

def get_subfolders(folder_path):
    subfolders = []
    if os.path.exists(folder_path):
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_dir():
                    subfolders.append(entry.name)
    return subfolders

def get_files_in_folder(folder_path):
    txt_files = []
    if os.path.exists(folder_path):
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.csv') and not entry.name.endswith('BR.csv'):
                    txt_files.append(entry.name)
    return txt_files

def get_subfolders_and_files(folder_path):
    txt_files = []
    
    if os.path.exists(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.bin'):
                    txt_files.append(os.path.join(root, file))
    
    return txt_files


@app.get("/")
def root():
    return {"message" : "Server running successfully"}

@app.post("/signup", summary="Sign Up")
def signup(userDetails : UserDetailsDto):
    logging.info(f"/signup called with user data : {userDetails}")
    username = userDetails.username
    password = userDetails.password
    displayName = userDetails.displayName
    age = userDetails.age
    gender = userDetails.gender
    userEmail = userDetails.userEmail
    contactInformation = userDetails.contactInformation
    medicalConditions = userDetails.medicalConditions
    medications = userDetails.medications
    fitnessGoals = userDetails.fitnessGoals
    fitnessPlan = userDetails.fitnessPlan
    chronicHealthConditions = userDetails.chronicHealthConditions
    medicationHistory = userDetails.medicationHistory
    dietaryHabits = userDetails.dietaryHabits
    sleepQuality = userDetails.sleepQuality
    notesComments = userDetails.notesComments
    
    currentDir = os.getcwd()
    userdbFile = os.path.join(currentDir, 'userdb.json')
    logging.info(f"reading userdb file...")
    userdb = dict(json.loads(open(userdbFile).read()))
    username = username.replace(" ","")
    if username in userdb.keys():
        logging.info(f"user alerady exist with username : {username}")
        returnMessage = "Username already exists please try again with another username"
        return PlainTextResponse(str(returnMessage), status_code=409)
    logging.info(f"Adding user to userdb file with username : {username}")
    userdb[username] = {
        "username" : username,
        "password" : password,
        "displayName" : displayName,
        "age" : age,
        "gender" : gender,
        "userEmail" : userEmail,
        "contactInformation" : contactInformation,
        "medicalConditions" : medicalConditions,
        "medications" : medications,
        "fitnessGoals" : fitnessGoals,
        "fitnessPlan" : fitnessPlan,
        "chronicHealthConditions" : chronicHealthConditions,
        "medicationHistory" : medicationHistory,
        "dietaryHabits" : dietaryHabits,
        "sleepQuality" : sleepQuality,
        "notesComments" : notesComments,
        
    }
    data = open(userdbFile,'w')
    logging.info(f"writing to file...")
    data.write(json.dumps(userdb))
    data.close()
    return PlainTextResponse(str("User Created Successfully"), status_code=200)



@app.post("/login", summary="Log in")
def login(loginDetails : LoginDetailsDto):
    logging.info(f"/login called with credentials : {loginDetails}")
    username = loginDetails.username
    password = loginDetails.password

    currentDir = os.getcwd()
    userdbFile = os.path.join(currentDir, 'userdb.json')
    logging.info(f"reading userdb file...")
    userdb = dict(json.loads(open(userdbFile).read()))
    username = username.replace(" ","")
    if username in userdb.keys() and password == userdb[username]['password']:
        logging.info(f"User found with userid: {username} and password: {password}")
        return PlainTextResponse(str("Login Successfully"), status_code=200)
    else:
        logging.info(f"User not found with userid: {username} and password: {password}")
        return PlainTextResponse(str("Invalid username or password"), status_code=409)


@app.post("/startSession", summary="Start Session")
def startSession(requestData:HeaderPayloadDto):
    logging.info(f'/sendData called with payload : {requestData}')
    currentDir = os.path.join(os.getcwd(),"allUsers")
    child_dir = os.path.join(currentDir, requestData.userId)
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = dict(json.loads(open(fn).read()))
    filePath = os.path.join(child_dir, requestData.deviceId)
    fileName = os.path.join(filePath, (str(requestData.sessionStartTime).replace('_','-').replace('.','-') + ".bin"))

    
    try:
        logging.info(f'Creating directory for user')
        createDirectory(currentDir,requestData.userId)
    except:
        pass
    try:
        logging.info(f'Creating directory for device')
        createDirectory(child_dir,requestData.deviceId)
        filesData[requestData.deviceId] = {'latest' : fileName, 'others' : []}
    except Exception as e:
        logging.error("Error : ",str(e))
        pass
    
    if not os.path.isfile(fileName):
        logging.info(f'New sessionStartTime received')
        filesData[requestData.deviceId]['latest'] = fileName
        filesData[requestData.deviceId]['others'].append(fileName)

    data = open(fn,'w')
    logging.info(f'Changing json file')
    data.write(json.dumps(filesData))
    data.close()

    logging.info(f'Writing data to file')
    file = open(fileName,"wb")
    file.close()
    return {'message' : 'File created Successfully!!'}


@app.post("/ongoingSession", summary="Ongoing Session (Sending Data)")
def ongoingSession(requestData:ReceiveDataPayloadDto):
    logging.info(f'/ongoingSession called with payload : {requestData}')
    if requestData.payload == []:
        logging.info(f'/ongoingSession called with empty payload')
        return {'message' : 'Empty data received'}
    currentDir = os.path.join(os.getcwd(),"allUsers")
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    fileName = filesData[requestData.deviceId]['latest']
    file = open(fileName,"ab")
    logging.info(f'/Writing data to file {fileName}')
    byte_list = struct.pack(f'{len(requestData.payload)}B', *requestData.payload)
    file.write(byte_list)
    file.close()
    return {'message' : 'Successfully added data to file!!'}


@app.post("/endSession", summary="End Session")
def endSession(payload : EndSessionPayloadDto):
    logging.info(f'/endSession called with deviceId : {payload.deviceId}')
    payload.sessionEndTime = payload.sessionEndTime.replace(':','-').replace('.','-')
    currentDir = os.path.join(os.getcwd(),"allUsers")
    filesDataPath = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(filesDataPath).read())
    latestFileName = filesData[payload.deviceId]['latest']
    startTimestamp = latestFileName.split('/')[-1].split('.')[0]
    deviceId = os.path.dirname(latestFileName)

    logging.info("converting bin to ascii and hr")
    os.system(f"python3 VS_ppg_proc_v004_20230907_1930.py -i {deviceId} -o {deviceId} -a /home/ubuntu/data/vsstreamcodec -f False")
    logging.info("ascii to bin converted successfully")
    
    logging.info("generating breath rate")
    os.system(f"python3 breath_darshan.py {deviceId}/output/result_PPI_{startTimestamp}.txt {deviceId} {deviceId}/{payload.deviceId}_BR.csv")
    logging.info("breath rate generated successfully")

    os.system(f"python3 HR.py --input {deviceId}/output/result_HR_HRV_{startTimestamp}.txt --output {deviceId}/{payload.deviceId}_{startTimestamp}_TO_{payload.sessionEndTime}.csv --bin {latestFileName} --breath {deviceId}/{payload.deviceId}_BR.csv")
    logging.info("csv file generated successfully")
    logging.info(f'Sending csv file at path: {deviceId} with name : {payload.deviceId}.csv')
    return FileResponse(os.path.join(deviceId, f"{payload.deviceId}_{startTimestamp}_TO_{payload.sessionEndTime}.csv"))

@app.get("/{userId}/devices", summary="Get list of devices by userId")
def getAllDevices(userId : str):
    logging.info(f"Fetching list of devices with userid: {userId}")
    currentDir = os.path.join(os.getcwd(),"allUsers") 
    folder_path = os.path.join(currentDir, userId)
    subfolders = get_subfolders(folder_path)
    logging.info(f"Sending list of devices with userid: {userId}")
    return subfolders

@app.get("/{userId}/{deviceId}/recordings", summary="Get list of recordings by userId and deviceId")
def getAllRecordings(userId : str, deviceId : str):
    logging.info(f"Fetching all recording of user: {userId} and device: {deviceId}")
    currentDir = os.path.join(os.getcwd(),"allUsers")
    folder_path = os.path.join(currentDir, userId)
    folder_path = os.path.join(folder_path, deviceId)
    subfolders = get_files_in_folder(folder_path)
    logging.info(f"Sending all recording of user: {userId} and device: {deviceId}")
    return subfolders

@app.get("/{userId}/{deviceId}/{recordingId}", summary="Get recording data by userId, deviceId, and recordingId")
def getRecordingByUserIdAndDeviceId(userId : str, deviceId : str, recordingId:str):
    logging.info(f"Fetching recording with userid: {userId} deviceid: {deviceId} and recording file: {recordingId}")
    currentDir = os.path.join(os.getcwd(),"allUsers")
    filePath = os.path.join(currentDir, f"{userId}/{deviceId}/{recordingId}")
    logging.info(f"Sending recording with userid: {userId} deviceid: {deviceId} and recording file: {recordingId}")
    return FileResponse(filePath)