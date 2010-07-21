#!/usr/bin/env python
from twisted.internet import gtk2reactor # for gtk-2.0
gtk2reactor.install()

from twisted.internet import reactor, protocol
from twisted.web.client import getPage
from twisted.internet import task
from twisted.python import log

import logging

from onetczat_lib import IRCProtocol, CamProtocol
from onetczat_client import IRCProfile, CamProfile

import os
import sys
import gobject
import gtk

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

class ImagesDemo(gtk.Window):
    pixbuf_loader = None 
    load_timeout = None
    image_stream = None

    def __init__(self, parent=None):
        gtk.Window.__init__(self)
	
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
	
	factory = IRCClientFactory(self.profile)
	reactor.connectTCP('213.180.130.192', 5015, factory)
	
        try:
            self.set_screen(parent.get_screen())
        except AttributeError:
            self.connect('destroy', lambda *w: gtk.main_quit())
        self.connect("destroy", self.cleanup_callback)
        self.set_title("OnetCzat Kamerki")
        self.set_default_size(400, 400)
        self.set_border_width(8)

        vbox = gtk.VBox(False, 8)
        vbox.set_border_width(8)
        #self.add(vbox)

        self.label = gtk.Label();
        self.label.set_markup("Logging in")
        vbox.pack_start(self.label, False, False, 0)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_IN)

        # The alignment keeps the frame from growing when users resize
        # the window
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(frame)
        vbox.pack_start(align, False, False, 0)
        
        self.image = gtk.Image()
        self.image.set_from_pixbuf(None)
        frame.add(self.image)
        
        hpaned = gtk.HPaned()
        hpaned.add1(vbox)

        vbox2 = gtk.VBox(False, 8)
        vbox2.set_border_width(8)

        slider = gtk.VScale()
        slider.set_inverted(True)
        slider.set_range(0, 100)
        slider.set_increments(1, 10)
        slider.set_digits(0)
        slider.set_size_request(34, 160)
        slider.set_value_pos(gtk.POS_BOTTOM)
        slider.set_value(5)

        # Events
        slider.connect('value-changed', self.updateRefreshFrequency)
        
        vbox2.pack_start(slider, False, False, 0)

        button = gtk.Button("Quit")
        button.connect_object("clicked", gtk.mainquit, self)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()

        vbox2.pack_start(button, False, False, 0)
        hpaned.add2(vbox2)

        # Sensitivity control
        self.add(hpaned)
        self.show_all()

    def onLoginSuccess(self):
	print 'Zalogowano!'
	self.updateLabel('Logged into OnetCzat. Logging to OnetCams...')
	#profile.getChannelList()
	self.profile.join('#scc')
	uokey = self.profile.getUOKEY()
	camfactory = CamClientFactory(self.camconn, self.account, uokey)
	reactor.connectTCP('212.244.48.54', 5008, camfactory)
    
    def onCamLoginSuccess(self):
	self.updateLabel('Logged into OnetCams. Choose a nick and double click on it!')
	print 'Zalogowano i mozemy pobierac pakiety z protokolu kamerek.'
	#self.camconn.subscribeCamera('cora6')
    
    def onCamImgRecv(self, nick, data):
	self.updateLabel('Receiving stream from %s' % (nick))
	self.updateImage(data)
	print 'pobrano obraz!'

    def onSubscribeDenied(self, nick):
	self.updateLabel('Canoot connect to user %s stream.' % (nick))

    def onNoSuchUser(self, nick):
	self.updateLabel('User %s is not logged in.' % (nick))

    def onUserGone(self, nick):
	self.updateLabel('User %s gone.' % (nick))

    def onUserList(self, data):
        pass
        #print data

    def onUserCountUpdate(self, data):
        data = data.split('\n')
        self.liststore.clear()
        for user in data:
            try:
                nick, watchers, unknown = user.split(' ')
                #print 'a:', user.split(' ')
                #print nick
                self.liststore.append([int(watchers), int(unknown), str(nick)])
            except:
                print 'Not possible for data: ', user

    def updateRefreshFrequency(self, widget):

        val = widget.get_value()

        print val


    def nickClicked(self, treeview, iter, tvc, foo):
        model=treeview.get_model()
        iter = model.get_iter(iter)
        nickname = model.get_value(iter, 2)
        if nickname:
            self.updateLabel('Fetching stream. Please wait a moment.')
            if self.watching == True:
                self.camconn.stopPing(self.watched_nick)
                self.camconn.unsubscribeCamera(self.watched_nick)
            self.camconn.subscribeCamera(nickname)
            self.camconn.startPing(nickname)
            self.watched_nick = nickname
            self.watching = True
        print nickname

    def updateLabel(self, text):
	self.label.set_markup(text)

    def updateImage(self, data):
	loader = gtk.gdk.PixbufLoader("jpeg")
	loader.write(data)
	pixbuf = loader.get_pixbuf()
	loader.close()
	self.image.set_from_pixbuf(pixbuf)

    def cleanup_callback(self, win):
#        if self.load_timeout != 0:
#            gtk.timeout_remove(self.load_timeout)
#            self.load_timeout = 0

        if self.pixbuf_loader is not None:
            self.pixbuf_loader.close()
            self.pixbuf_loader = None

        if self.image_stream is not None:
            self.image_stream.close()
            self.image_stream = None

        self.camconn.stopPing(self.watched_nick)
        self.camconn.unsubscribeCamera(self.watched_nick)
        gtk.main_quit()
	reactor.stop()
        sys.exit(1)


def main():
    ImagesDemo()
    #gtk.main()
    reactor.run()

if __name__ == '__main__':
    main()
