import logging
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import uvicorn
import json


FORMAT = "%(levelname)s:%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

app = FastAPI()

class HeaderPayloadDto(BaseModel):
    device_id : str
    user_id : str
    timestamp : str

class ReceiveDataPayloadDto(BaseModel):
    device_id : str
    payload : str
    frequency : str

def createDirectory(parent_dir,directory):
    path = os.path.join(parent_dir, directory) 
    os.makedirs(path)

@app.post("/sendData")
def sendData(requestData:ReceiveDataPayloadDto):
    logging.info(f'/sendData called with payload : {requestData}')
    currentDir = os.getcwd()
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    fileName = filesData[requestData.device_id]['latest']
    file = open(fileName,"a")
    logging.info(f'/Writing data to file {fileName}')
    file.write(requestData.payload)
    file.close()
    return {'message' : 'Successfully added data to file!!'}


@app.post("/sendHeader")
def sendHeader(requestData:HeaderPayloadDto):
    logging.info(f'/sendData called with payload : {requestData}')
    currentDir = os.getcwd()
    child_dir = os.path.join(currentDir, requestData.user_id) 
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    filePath = os.path.join(child_dir, requestData.device_id) 
    fileName = os.path.join(filePath, "Session_" + (str(requestData.timestamp).replace(':','-') + ".txt"))

    try:
        logging.info(f'Creating directories for user and device')
        createDirectory(currentDir,requestData.user_id)
        createDirectory(child_dir,requestData.device_id)
        filesData[requestData.device_id] = {'latest' : fileName, 'others' : []}
    except:
        pass

    if not os.path.isfile(fileName):
        logging.info(f'New timestamp received')
        filesData[requestData.device_id]['latest'] = fileName
        filesData[requestData.device_id]['others'].append(fileName)
        
    data = open(fn,'w')
    logging.info(f'Changing json file')
    data.write(json.dumps(filesData))
    data.close()

    logging.info(f'Writing data to file')
    file = open(fileName,"w")
    file.close()
    return {'message' : 'File created Successfully!!'}

@app.get("/getOutput/{deviceId}")
def getOutput(deviceId:str):
    logging.info(f'/getOutput called with deviceId : {deviceId}')
    currentDir = os.getcwd()
    fn = os.path.join(currentDir, 'filesData.json')
    filesData = json.loads(open(fn).read())
    fileName = filesData[deviceId]['latest']
    path = os.path.dirname(fileName)

    logging.info(f'Sending csv file at path: {path} with name : {deviceId}.csv')
    return FileResponse(os.path.join(path, deviceId+".csv") )


if __name__ == '__main__':
    uvicorn.run(app,host='0.0.0.0',port=8000)