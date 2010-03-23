

class IRCProfile(object):

    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.__hashelem = None
        self.__contacts = {}
        self.__groups = {}
        self.__connection = None

    def _loginSuccess(self, conn, *args, **kwargs):
        self.__connection = conn
        self.onLoginSuccess()
        return self

    # high-level interface
    @property
    def connected(self):
        """Is the profile currently used in an active connection"""
        return self.__connection is not None

    # stuff that user can use
    def getChannelList(self):
        self.__connection.sendData('SLIST')

    def join(self, room_id):
        self.__connection.sendData('join '+room_id)
        
    def getUOKEY(self):
        return self.__connection.uokey

    def sendMsg(self, room_id, formatting, text):
        self.__connection.sendData('privmsg '+str(room_id)+' :'+str(formatting+text))


    def startPriv(self, nick):
        self.__connection.sendData('PRIV '+str(nick))

    def requestInfo(self, nick):
        #self.__connection.sendData('NSINFO '+str(nick)+' s')
        self.__connection.sendData('NS INFO '+str(nick))
        
    def exitChannel(self, room_id):
        self.__connection.sendData('PART :'+str(room_id))

    def disconnect(self):
        self.__connection.transport.loseConnection()

    # stuff that should be implemented by user
    def onLoginSuccess(self):
        """Called when login is completed."""
        pass

    def onLoginFailure(self, reason):
        """Called after an unsuccessful login."""
        pass

    def onTopicRecv(self, room_id, topic):
        pass

    def onNicksRecv(self, room_id, nicks):
        pass

    def onMsgRecv(self, room_id, nick, msg, formatting):
        pass

    def onNickQuit(self, nick):
        pass

    def onNickJoin(self, nick, room_id, flags):
        pass

    def onNickPart(self, nick, room_id):
        pass

    def userInfoRecv(self, nick, data):
        pass

    def userModeRecv(self, nick, mode):
        pass

    @property
    def contacts(self):
        return self.__contacts.itervalues()

    @property
    def groups(self):
        return self.__groups.itervalues()


class CamProfile(object):
    def __init__(self, account):
        self.account = account
        self.__connection = None

    def _loginSuccess(self, conn, *args, **kwargs):
        self.__connection = conn
        self.onLoginSuccess()
        return self

    # high-level interface
    @property
    def connected(self):
        """Is the profile currently used in an active connection"""
        return self.__connection is not None

    # stuff that user can use
    def subscribeCamera(self, nick):
        self.__connection.sendData('SUBSCRIBE_BIG * %s' % (nick))

    def unsubscribeCamera(self, nick):
        self.__connection.sendData('UNSUBSCRIBE_BIG * %s' % (nick))

    def startPing(self, nick):
        self.__connection.startPing(nick)

    def stopPing(self, nick):
        self.__connection.stopPing(nick)

    def sendMsg(self, room_id, formatting, text):
        self.__connection.sendData('privmsg '+str(room_id)+' :'+str(formatting+text))
        
    def exitChannel(self, room_id):
        self.__connection.sendData('PART :'+str(room_id))

    def disconnect(self):
        self.__connection.transport.loseConnection()

    # stuff that should be implemented by user
    def onLoginSuccess(self):
        """Called when login is completed."""
        pass

    def onLoginFailure(self, reason):
        """Called after an unsuccessful login."""
        pass
    
    def onSubscribeDenied(self, nick):
        pass
    
    def onNoSuchUser(self, nick):
        pass

    def onUserGone(self, nick):
        pass

    def onUserCountUpdate(self, data):
        pass

    def onUserList(self, data):
        pass

    def onImgRecv(self, nick, data):
        pass
