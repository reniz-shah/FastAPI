import logging
from fastapi import FastAPI
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


def createDirectory(parent_dir,directory):
    path = os.path.join(parent_dir, directory)
    os.makedirs(path)

@app.get("/")
def root():
    return {"message" : "App running successfully"}

@app.post("/sendData")
def sendData(requestData:ReceiveDataPayloadDto):
    logging.info(f'/sendData called with payload : {requestData}')
    currentDir = os.getcwd()
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    fileName = filesData[requestData.deviceId]['latest']
    file = open(fileName,"ab")
    logging.info(f'/Writing data to file {fileName}')
    byte_list = struct.pack(f'{len(requestData.payload)}B', *requestData.payload)
    file.write(byte_list)
    file.close()
    return {'message' : 'Successfully added data to file!!'}


@app.post("/sendHeader")
def sendHeader(requestData:HeaderPayloadDto):
    logging.info(f'/sendData called with payload : {requestData}')
    currentDir = os.getcwd()
    child_dir = os.path.join(currentDir, requestData.userId)
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = dict(json.loads(open(fn).read()))
    filePath = os.path.join(child_dir, requestData.deviceId)
    fileName = os.path.join(filePath, "Session_" + (str(requestData.sessionStartTime).replace(':','-').replace('.','-') + ".bin"))

    try:
        logging.info(f'Creating directories for user and device')
        createDirectory(currentDir,requestData.userId)
        createDirectory(child_dir,requestData.deviceId)
        filesData[requestData.deviceId] = {'latest' : fileName, 'others' : []}
    except Exception as e:
        return {"error" : e}
    
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

@app.get("/getOutput")
def getOutput(deviceId:str):
    logging.info(f'/getOutput called with deviceId : {deviceId}')
    currentDir = os.getcwd()
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    fileName = filesData[deviceId]['latest']
    path = os.path.dirname(fileName)

    logging.info(f'Sending csv file at path: {path} with name : {deviceId}.csv')
    return FileResponse(os.path.join(path, deviceId+".csv") )

@app.get("/getAllDevicesByUserId")
def getAllDevices(userId : str):
    return {'userId' : userId}