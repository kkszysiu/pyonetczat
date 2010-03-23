from twisted.internet import reactor, protocol
from twisted.web.client import getPage
from twisted.internet import task
from twisted.python import log

import logging

from onetczat_lib import IRCProtocol, CamProtocol
from onetczat_client import IRCProfile, CamProfile

__all__ = ['OnetCzatConnection']

logger = logging.getLogger('OnetCzat.Connection')

class IRCClientFactory(protocol.ClientFactory):
    def __init__(self, config):
        self.config = config

    def buildProtocol(self, addr):
        # connect using current selected profile
        #self.resetDelay()
        return IRCProtocol(self.config)

    def startedConnecting(self, connector):
        logger.info('Started to connect.')

    def clientConnectionLost(self, connector, reason):
        logger.info('Lost connection.  Reason: %s' % (reason))
        #protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        #connector.connect()
        if reactor.running:
            reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        logger.info('Connection failed. Reason: %s' % (reason))
        #protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        if reactor.running:
            reactor.stop()

class CamClientFactory(protocol.ClientFactory):
    def __init__(self, conn, nick, uokey):
        self.nick = nick
        self.uokey = uokey
        self.conn = conn

    def buildProtocol(self, addr):
        # connect using current selected profile
        #self.resetDelay()
        return CamProtocol(self.conn, self.nick, self.uokey)

    def startedConnecting(self, connector):
        logger.info('Started to connect.')

    def clientConnectionLost(self, connector, reason):
        logger.info('Lost connection.  Reason: %s' % (reason))
        #protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        #connector.connect()
        #if reactor.running:
        #    reactor.stop()
        print reason

    def clientConnectionFailed(self, connector, reason):
        logger.info('Connection failed. Reason: %s' % (reason))
        #protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        #if reactor.running:
        #    reactor.stop()
        print reason

def onLoginSuccess():
    print 'Zalogowano!'
    #profile.getChannelList()
    profile.join('#scc')
    uokey = profile.getUOKEY()
    camfactory = CamClientFactory(camconn, account, uokey)
    reactor.connectTCP('212.244.48.54', 5008, camfactory)

def onCamLoginSuccess():
    print 'Zalogowano i mozemy pobierac pakiety z protokolu kamerek.'
    camconn.subscribeCamera('LenCia')

def onCamImgRecv(nick, data):
    print 'pobrano obraz!'

account='kkszysiu'
password='xxxx'

profile = IRCProfile(account, password)
profile.onLoginSuccess = onLoginSuccess

camconn = CamProfile(account)
camconn.onLoginSuccess = onCamLoginSuccess
camconn.onImgRecv = onCamImgRecv


factory = IRCClientFactory(profile)
reactor.connectTCP('213.180.130.192', 5015, factory)
#camfactory = CamClientFactory(camconn, account, 'mTtJbwM7bmtQmEQN017nMFFLmfxh6ZNK')
#reactor.connectTCP('212.244.48.54', 5008, camfactory)
reactor.run()
#
#profile.onLoginSuccess = self.on_loginSuccess
#profile.onLoginFailure = self.on_loginFailed
#profile.onContactStatusChange = self.on_updateContact
#profile.onMessageReceived = self.on_messageReceived
