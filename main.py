import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
    userid : str
    name : str
    age : int
    height : float
    weight : float
    password : str

class LoginDetailsDto(BaseModel):
    userid : str
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
    userid = userDetails.userid
    name = userDetails.name
    age = userDetails.age
    height = userDetails.height
    weight = userDetails.weight
    password = userDetails.password

    currentDir = os.getcwd()
    userdbFile = os.path.join(currentDir, 'userdb.json')
    userdb = dict(json.loads(open(userdbFile).read()))
    userid = userid.replace(" ","")
    if userid in userdb.keys():
        raise HTTPException(status_code=409, detail="User Id already exists please try again with another user id")
    userdb[userid] = {
        "name" : name,
        "age" : age,
        "height" : height,
        "weight" : weight,
        "password" : password,
    }
    data = open(userdbFile,'w')
    data.write(json.dumps(userdb))
    data.close()
    return {'message' : "User Created Successfully"}



@app.post("/login", summary="Log in")
def login(loginDetails : LoginDetailsDto):
    userid = loginDetails.userid
    password = loginDetails.password

    currentDir = os.getcwd()
    userdbFile = os.path.join(currentDir, 'userdb.json')
    userdb = dict(json.loads(open(userdbFile).read()))
    userid = userid.replace(" ","")
    if userid in userdb.keys() and password == userdb[userid]['password']:
        return {'isvalid':True}
    else:
        raise HTTPException(status_code=409, detail="Invalid user id or password")


@app.post("/startSession", summary="Start Session")
def startSession(requestData:HeaderPayloadDto):
    logging.info(f'/sendData called with payload : {requestData}')
    currentDir = os.path.join(os.getcwd(),"allUsers")
    child_dir = os.path.join(currentDir, requestData.userId)
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = dict(json.loads(open(fn).read()))
    filePath = os.path.join(child_dir, requestData.deviceId)
    fileName = os.path.join(filePath, (str(requestData.sessionStartTime).replace('_','-').replace('.','-') + ".bin"))

    
    logging.info(f'Creating directories for user and device')
    try:
        createDirectory(currentDir,requestData.userId)
    except:
        pass
    try:
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
    logging.info(f'/sendData called with payload : {requestData}')
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
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    fileName = filesData[payload.deviceId]['latest']
    file = fileName.split('/')[-1].split('.')[0]
    path = os.path.dirname(fileName)
    logging.info("converting bin to ascii and hr")
    os.system(f"python3 VS_ppg_proc_v004_20230907_1930.py -i {path} -o {path} -a /home/ubuntu/data/vsstreamcodec -f False")
    logging.info("ascii to bin converted successfully")
    logging.info("generating breath rate")
    os.system(f"python3 breath_darshan.py {path}/output/result_PPI_{file}.txt {path} {path}/{payload.deviceId}_BR.csv")
    os.system(f"python3 HR.py --input {path}/output/result_HR_HRV_{file}.txt --output {path}/{payload.deviceId}_{file}_TO_{payload.sessionEndTime}.csv --bin {fileName} --breath {path}/{payload.deviceId}_BR.csv")
    logging.info("breath rate generated successfully")
    logging.info(f'Sending csv file at path: {path} with name : {payload.deviceId}.csv')
    return FileResponse(os.path.join(path, f"{payload.deviceId}_{file}_TO_{payload.sessionEndTime}.csv") )

@app.get("/{userId}/devices", summary="Get list of devices by userId")
def getAllDevices(userId : str):
    currentDir = os.path.join(os.getcwd(),"allUsers")
    folder_path = os.path.join(currentDir, userId)
    subfolders = get_subfolders(folder_path)
    return subfolders

@app.get("/{userId}/{deviceId}/recordings", summary="Get list of recordings by userId and deviceId")
def getAllRecordings(userId : str, deviceId : str):
    currentDir = os.path.join(os.getcwd(),"allUsers")
    folder_path = os.path.join(currentDir, userId)
    folder_path = os.path.join(folder_path, deviceId)
    subfolders = get_files_in_folder(folder_path)
    return subfolders

@app.get("/{userId}/{deviceId}/{recordingId}", summary="Get recording data by userId, deviceId, and recordingId")
def getRecordingByUserIdAndDeviceId(userId : str, deviceId : str, recordingId:str):
    currentDir = os.path.join(os.getcwd(),"allUsers")
    filePath = os.path.join(currentDir, f"{userId}/{deviceId}/{recordingId}")
    return FileResponse(filePath)