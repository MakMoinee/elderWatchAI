class Devices:
    def __init__(self):
        self.deviceID = 0
        self.userID = 0
        self.ip = ""
        self.username = ""
        self.password = ""

    def getDeviceID(self):
        return self.deviceID
    
    def getUserID(self):
        return self.userID
    
    def getUsername(self):
        return self.username
    
    def getPassword(self):
        return self.password
    
    def getIP(self):
        return self.ip
    
    def setDeviceID(self,deviceID):
        self.deviceID = deviceID
    
    def setUserID(self,userID):
        self.userID = userID
    
    def setUsername(self,username):
        self.username = username
    
    def setPassword(self,password):
        self.password = password
    
    def setIP(self,ip):
        self.ip = ip