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


class AuthDialog(object):
    def responseToDialog(self, entry, dialog, response):
        dialog.response(response)
        print 'responseToDialog'
    def getText(self):
        #base this on a message dialog
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_markup('Please enter your <b>Onet Czat</b> login info:')
        #create the text input field
        entry = gtk.Entry()
        #allow the user to press enter to do ok
        entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)

        entry2 = gtk.Entry()
        #allow the user to press enter to do ok
        entry2.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
        #create a horizontal box to pack the entry and a label
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Login:"), False, 5, 5)
        hbox.pack_end(entry)
        hbox2 = gtk.HBox()
        hbox2.pack_start(gtk.Label("Password:"), False, 5, 5)
        hbox2.pack_end(entry2)
        #some secondary text
        dialog.format_secondary_markup("")
        #add it and show it
        dialog.vbox.pack_start(hbox, True, True, 0)
        dialog.vbox.pack_start(hbox2, True, True, 0)
        dialog.show_all()
        #go go go
        dialog.run()
        text = entry.get_text()
        text2 = entry2.get_text()
        dialog.destroy()
        CameraWindow(None, text, text2)
        print text
        return text


class CameraWindow(gtk.Window):
    pixbuf_loader = None
    load_timeout = None
    image_stream = None

    def __init__(self, parent=None, user=None, password=None):
        gtk.Window.__init__(self)
	
	self.account=user
	self.password=password
	
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
        self.add(vbox)

        self.label = gtk.Label();
        self.label.set_markup("<u>Logging in</u>")
        vbox.pack_start(self.label, False, False, 0)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_IN)

        # The alignment keeps the frame from growing when users resize
        # the window
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        align.add(frame)
        vbox.pack_start(align, False, False, 0)

        # Create an empty image for now; the progressive loader
        # will create the pixbuf and fill it in.
	#img = open('aa.jpg')
	#data = img.read()
	#img.close()
	#loader = gtk.gdk.PixbufLoader("jpeg")
	#loader.write(data)
	#loader.close()
	#pixbuf = loader.get_pixbuf()
	
        self.image = gtk.Image()
        self.image.set_from_pixbuf(None)
        frame.add(self.image)

        self.liststore = gtk.ListStore(int, int, str)
        self.tree = gtk.TreeView(model=self.liststore)
        self.tree.connect("row-activated", self.nickClicked, None)

        column_w = gtk.TreeViewColumn('Watchers')
        column_w.set_clickable(True)
        column_w.set_sort_column_id(0)
        column_w.set_resizable(True)


        column_u = gtk.TreeViewColumn('Unknown')
        column_n = gtk.TreeViewColumn('Nick')

        self.tree.append_column(column_w)
        self.tree.append_column(column_u)
        self.tree.append_column(column_n)

        cell_w = gtk.CellRendererText()
        cell_u = gtk.CellRendererText()
        cell_n = gtk.CellRendererText()

        column_w.pack_start(cell_w)
        column_u.pack_start(cell_u)
        column_n.pack_start(cell_n)

        column_w.add_attribute(cell_w, 'text', 0)
        column_u.add_attribute(cell_u, 'text', 1)
        column_n.add_attribute(cell_n, 'text', 2)

        sw = gtk.ScrolledWindow()
        sw.add(self.tree)
        vbox.add(sw)

        # Sensitivity control

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
    auth = AuthDialog()
    auth.getText()
    #ImagesDemo()
    #gtk.main()
    reactor.run()

if __name__ == '__main__':
    main()
