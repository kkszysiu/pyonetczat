#!/usr/bin/env python

from twisted.internet import reactor, protocol
from twisted.web.client import getPage
from twisted.internet import task
from twisted.python import log

import logging
import aalib
import Image
from cStringIO import StringIO

from onetczat_lib import IRCProtocol, CamProtocol
from onetczat_client import IRCProfile, CamProfile

import os
import sys

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

class ImagesDemo(object):
    def __init__(self, parent=None):
	self.account='login'
	self.password='password'
	
	self.profile = IRCProfile(self.account, self.password)
	self.profile.onLoginSuccess = self.onLoginSuccess
	
	self.camconn = CamProfile(self.account)
	self.camconn.onLoginSuccess = self.onCamLoginSuccess
	self.camconn.onImgRecv = self.onCamImgRecv
	self.camconn.onSubscribeDenied = self.onSubscribeDenied
	self.camconn.onNoSuchUser = self.onNoSuchUser
	self.camconn.onUserGone = self.onUserGone
        self.camconn.onUserCountUpdate = self.onUserCountUpdate
        self.camconn.onUserList = self.onUserList

        self.watching = False
        self.watched_nick = None
        
        self.screen = aalib.AsciiScreen(width=320, height=240)
	
	factory = IRCClientFactory(self.profile)
	reactor.connectTCP('213.180.130.192', 5015, factory)

    def onLoginSuccess(self):
	print 'Zalogowano!'
	print ('Logged into OnetCzat. Logging to OnetCams...')
	#profile.getChannelList()
	self.profile.join('#scc')
	uokey = self.profile.getUOKEY()
	camfactory = CamClientFactory(self.camconn, self.account, uokey)
	reactor.connectTCP('212.244.48.54', 5008, camfactory)
    
    def onCamLoginSuccess(self):
	print ('Logged into OnetCams. Choose a nick and double click on it!')
	print 'Zalogowano i mozemy pobierac pakiety z protokolu kamerek.'
	#self.camconn.subscribeCamera('cora6')
        self.camconn.subscribeCamera('kocica35')
        self.camconn.startPing('kocica35')
    
    def onCamImgRecv(self, nick, data):
	print ('Receiving stream from %s' % (nick))
	self.updateImage(data)
	print 'pobrano obraz!'

    def onSubscribeDenied(self, nick):
	print ('Canoot connect to user %s stream.' % (nick))

    def onNoSuchUser(self, nick):
	print ('User %s is not logged in.' % (nick))

    def onUserGone(self, nick):
	print ('User %s gone.' % (nick))

    def onUserList(self, data):
        pass
        #print data

    def onUserCountUpdate(self, data):
        data = data.split('\n')
        for user in data:
            try:
                nick, watchers, unknown = user.split(' ')
                #print 'a:', user.split(' ')
                #print nick
            except:
                print 'Not possible for data: ', user


    def nickClicked(self, treeview, iter, tvc, foo):
        model=treeview.get_model()
        iter = model.get_iter(iter)
        nickname = model.get_value(iter, 2)
        if nickname:
            print ('Fetching stream. Please wait a moment.')
            if self.watching == True:
                self.camconn.stopPing(self.watched_nick)
                self.camconn.unsubscribeCamera(self.watched_nick)
            self.camconn.subscribeCamera(nickname)
            self.camconn.startPing(nickname)
            self.watched_nick = nickname
            self.watching = True
        print nickname

    def updateImage(self, data):
        self.fp = StringIO(data)
        self.image = Image.open(fp).convert('L').resize(self.screen.virtual_size)
        self.screen.put_image((0, 0), image)
        print self.screen.render()


def main():
    ImagesDemo()
    reactor.run()

if __name__ == '__main__':
    main()
