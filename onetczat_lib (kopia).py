# -*- coding: utf-8
from twisted.internet.protocol import Protocol
from twisted.internet import task
import twisted.python.log as tlog

import time

from twisted.protocols import basic

from twisted.internet import reactor
from pprint import pformat

from twisted.internet.defer import Deferred
from twisted.web.http_headers import Headers
from twisted.internet.defer import succeed

from twisted.internet import task

from twisted.web.iweb import IBodyProducer
from twisted.web.client import Agent

from twisted.python import log

from zope.interface import implements

import sys
import re
import urllib
import logging

from xml.dom import minidom

#helper modules
import consts

__all__ = ['IRCProtocol', 'CamProtocol']

logger = logging.getLogger('OnetCzat.Connection')

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10
        self.body = ''

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            self.body = self.body+display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        #print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(self.body)


class OnetAuth(object):
    def __init__(self, nickname, password):
        self.nickname = nickname
        self.password = password

        self.authorised = Deferred()

        self.agent = Agent(reactor)

    def auth(self, s):
      stringbuffer = ""
      ai = []
      pomoc = []

      f1 = [
            29, 43, 7, 5, 52, 58, 30, 59, 26, 35,
            35, 49, 45, 4, 22, 4, 0, 7, 4, 30, 51,
            39, 16, 6, 32, 13, 40, 44, 14, 58, 27,
            41, 52, 33, 9, 30, 30, 52, 16, 45, 43,
            18, 27, 52, 40, 52, 10, 8, 10, 14, 10,
            38, 27, 54, 48, 58, 17, 34, 6, 29, 53,
            39, 31, 35, 60, 44, 26, 34, 33, 31, 10,
            36, 51, 44, 39, 53, 5, 56
        ]
      f2 = [
            7, 32, 25, 39, 22, 26, 32, 27, 17, 50,
            22, 19, 36, 22, 40, 11, 41, 10, 10, 2,
            10, 8, 44, 40, 51, 7, 8, 39, 34, 52, 52,
            4, 56, 61, 59, 26, 22, 15, 17, 9, 47, 38,
            45, 10, 0, 12, 9, 20, 51, 59, 32, 58, 19,
            28, 11, 40, 8, 28, 6, 0, 13, 47, 34, 60,
            4, 56, 21, 60, 59, 16, 38, 52, 61, 44, 8,
            35, 4, 11
        ]
      f3 = [
            60, 30, 12, 34, 33, 7, 15, 29, 16, 20,
            46, 25, 8, 31, 4, 48, 6, 44, 57, 16,
            12, 58, 48, 59, 21, 32, 2, 18, 51, 8,
            50, 29, 58, 6, 24, 34, 11, 23, 57, 43,
            59, 50, 10, 56, 27, 32, 12, 59, 16, 4,
            40, 39, 26, 10, 49, 56, 51, 60, 21, 37,
            12, 56, 39, 15, 53, 11, 33, 43, 52, 37,
            30, 25, 19, 55, 7, 34, 48, 36
        ]
      p1 = [
            11, 9, 12, 0, 1, 4, 10, 13, 3,
            6, 7, 8, 15, 5, 2, 14
        ]
      p2 = [
            1, 13, 5, 8, 7, 10, 0, 15, 12, 3,
            14, 11, 2, 9, 6, 4
        ]


      if len(s) < 16:
        return "(key to short)"

      i = 0
      while i < 16:
        c = s[i]
        if c > '9':
          if c > 'Z':
            ai.insert(i, (ord(c) - 97) + 36)
          else:
            ai.insert(i, (ord(c) - 65) + 10)
        else:
          ai.insert(i, ord(c) - 48)
        i = i + 1

      i = 0
      while i < 16:
        ai[i] = f1[ai[i] + i]
        i = i + 1
      ai1 = ai

      i = 0
      while i < 16:
        pomoc.insert(i, (ai[i] + ai1[p1[i]]) % 62)
        i = i + 1
      ai = pomoc

      i = 0
      while i < 16:
        ai[i] = f2[ai[i] + i]
        i = i + 1
      ai1 = ai

      pomoc = []
      i = 0
      while i < 16:
        pomoc.insert(i, (ai[i] + ai1[p2[i]]) % 62)
        i = i + 1
      ai = pomoc

      i = 0
      while i < 16:
        ai[i] = f3[ai[i] + i]
        i = i + 1

      i = 0
      while i < 16:
        j = ai[i]
        if j >= 10:
          if j >= 36:
            ai[i] = (97 + j) - 36
          else:
            ai[i] = (65 + j) - 10
        else:
          ai[i] = 48 + j
        stringbuffer = stringbuffer + chr(ai[i])
        i = i + 1

      return stringbuffer

    def authorise(self):
        d = self.agent.request(
            'GET',
            'http://kropka.onet.pl/_s/kropka/1?DV=czat',
            None,
            None)

        d.addCallback(self.cbGetFirstCookie)
        d.addErrback(self.cbShutdown)

    def cbGetFirstCookie(self, response):
        onet_ubi_cookie = response.headers.getRawHeaders('Set-Cookie')[0]
        onetzuo_ticket_cookie = response.headers.getRawHeaders('Set-Cookie')[1]
        onet_cid_cookie = response.headers.getRawHeaders('Set-Cookie')[2]
        #onet_sgn_cookie = response.headers.getRawHeaders('Set-Cookie')[3]

        onet_ubi_match = re.search("onet_ubi=(.*?);", onet_ubi_cookie)
        if onet_ubi_match:
            onet_ubi_result = onet_ubi_match.group()
        else:
            onet_ubi_result = None

        onetzuo_ticket_match = re.search("onetzuo_ticket=(.*?);", onetzuo_ticket_cookie)
        if onetzuo_ticket_match:
            onetzuo_ticket_result = onetzuo_ticket_match.group()
        else:
            onetzuo_ticket_result = None

        onet_cid_match = re.search("onet_cid=(.*?);", onet_cid_cookie)
        if onet_cid_match:
            onet_cid_result = onet_cid_match.group()
        else:
            onet_cid_result = None

        #onet_sgn_match = re.search("onet_sgn=(.*?);", onet_sgn_cookie)
        #if onet_sgn_match:
        #    onet_sgn_result = onet_sgn_match.group()
        #else:
        #    onet_sgn_result = None

        if onet_ubi_result != None and onetzuo_ticket_result != None and onet_cid_result != None:
            finished = Deferred()
            response.deliverBody(BeginningPrinter(finished))
            finished.addCallback(self.cbGetFirstCookieSuccess, onet_ubi_result, onetzuo_ticket_result, onet_cid_result)
            finished.addErrback(self.cbShutdown)
            return finished
        else:
            self.authorise()

    def cbGetFirstCookieSuccess(self, result, onet_ubi_result, onetzuo_ticket_result, onet_cid_result):
        #now we need to have second cookie with sid
        cookie = onet_ubi_result+' '+onetzuo_ticket_result+' '+onet_cid_result
        headers = {}
        headers['Cookie'] = [cookie]
        headers['Host'] = ['czat.onet.pl']
        headers = Headers(headers)

        d = self.agent.request(
            'GET',
            'http://czat.onet.pl/myimg.gif',
            headers,
            None)

        d.addCallback(self.cbGetSecondCookie, cookie)
        d.addErrback(self.cbShutdown)


    def cbGetSecondCookie(self, response, cookie):
        onet_sid_cookie = response.headers.getRawHeaders('Set-Cookie')[0]

        onet_sid_match = re.search("onet_sid=(.*?);", onet_sid_cookie)
        if onet_sid_match:
            onet_sid_result = onet_sid_match.group()
        else:
            onet_sid_result = None


        if onet_sid_result != None:
            cookie = cookie+' '+onet_sid_result
            finished = Deferred()
            response.deliverBody(BeginningPrinter(finished))
            finished.addCallback(self.cbGetSecondCookieSuccess, cookie)
            finished.addErrback(self.cbShutdown)
            return finished
        else:
            self.authorise()

    def cbGetSecondCookieSuccess(self, result, cookie):
        if self.nickname[0] != '~':
            postvars = "r=&url=&login=%s&haslo=%s&ok=Ok" % (self.nickname, self.password)
            body = StringProducer(str(postvars))

            headers = {}
            headers['Cache-Control'] = ['no-cache']
            headers['Pragma'] = ['no-cache']
            headers['Host'] = ['secure.onet.pl']
            headers['Connection'] = ['keep-alive']
            headers['User-Agent'] = ['Mozilla/4.0 (FreeBSD) Java-brak ;)']
            headers['Content-Type'] = ['application/x-www-form-urlencoded']
            headers['Cookie'] = [cookie]
            headers = Headers(headers)

            d = self.agent.request(
                'POST',
                'http://secure.onet.pl/index.html',
                headers,
                body)

            d.addCallback(self.postLoginInfo, cookie)
            d.addErrback(self.cbShutdown)
        else:
            self.postAuth(cookie, True)

    def postLoginInfo(self, result, cookie):
        #print 'postLoginInfo()'
        self.postAuth(cookie, False)

    def postAuth(self, cookie, anonymous=True):
        #print 'cookie: ', cookie
        #print 'postAuth(%s)' % (anonymous)
        nickname = self.nickname
        if anonymous != True:
            postvars = "api_function=getUoKey&params=a:3:{s:4:\"nick\";s:%d:\"%s\";s:8:\"tempNick\";i:0;s:7:\"version\";s:22:\"1.0(20090306-1441 - R)\";}" % (len(nickname), nickname)
        else:
            postvars = "api_function=getUoKey&params=a:3:{s:4:\"nick\";s:%d:\"%s\";s:8:\"tempNick\";i:1;s:7:\"version\";s:22:\"1.0(20090306-1441 - R)\";}" % (len(nickname) - 1, nickname[1:])

        body = StringProducer(str(postvars))

        headers = {}
        headers['Cache-Control'] = ['no-cache']
        headers['Pragma'] = ['no-cache']
        headers['Host'] = ['czat.onet.pl']
        headers['Connection'] = ['close']
        headers['User-Agent'] = ['Mozilla/4.0 (FreeBSD) Java-brak ;)']
        headers['Accept'] = ['text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2']
        #headers['Content-Length'] = [body.length]
        headers['Content-Type'] = ['application/x-www-form-urlencoded']
        headers['Cookie'] = [cookie]
        headers = Headers(headers)

        d = self.agent.request(
            'POST',
            'http://czat.onet.pl/include/ajaxapi.xml.php3',
            headers,
            body)

        d.addCallback(self.cbPostAuth, cookie)
        d.addErrback(self.cbShutdown)

    def cbPostAuth(self, response, cookie):
        #print 'cbPostAuth()'
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished))
        finished.addCallback(self.cbPostAuthSuccess, cookie)
        finished.addErrback(self.cbShutdown)
        return finished

    def cbPostAuthSuccess(self, result, cookie):
        #print 'cbPostAuthSuccess()'
        result = result.decode('ISO-8859-2').encode('UTF-8')

        xml_root = minidom.parseString(result)
        #print xml_root.firstChild.toxml()
        try:
            bool(xml_root.getElementsByTagName('error')[0].attributes['err_code'].value)
            uokey = xml_root.getElementsByTagName('uoKey')[0].firstChild.data

            self.authorised.addCallback(self._onAuthorised, self.nickname, self.password, uokey)
            self.authorised.callback(self)

        except:
            print 'blad'


    def cbShutdown(self, ignored):
        #reactor.stop()
        logger.info("Something went wrong.")
        logger.info('cbShutdown: ', ignored)

    def _onAuthorised(self, result, nickname, password, uokey):
        return self.onAuthorised(nickname, password, uokey)


    def onAuthorised(nickname, password, uokey):
        pass

class AvatarFetcher(object):
    def __init__(self, nick, url):
        self.nick = nick
        self.url = url
        self.agent = Agent(reactor)

    def get(self):
        d = self.agent.request(
            'GET',
            self.url,
            None,
            None)

        d.addCallback(self.cbGetContent)
        d.addErrback(self.cbShutdown)

    def cbGetContent(self, response):
#        print 'Response version:', response.version
#        print 'Response code:', response.code
#        print 'Response phrase:', response.phrase
#        print 'Response headers:'
#        print pformat(list(response.headers.getAllRawHeaders()))
        mime = response.headers.getRawHeaders('Content-Type')[0]
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished))
        finished.addCallback(self.cbGetContentSuccess, mime)
        finished.addErrback(self.cbShutdown)
        return finished

    def cbGetContentSuccess(self, content, mime):
        self.onAvatarFetched(self.nick, mime, content)

    def onAvatarFetched(nick, mime, data):
        pass

    def cbShutdown(self, ignored):
        #reactor.stop()
        logger.info("Something went wrong.")
        logger.info('cbShutdown: ', ignored)

class IRCProtocol(basic.LineReceiver):

    def __init__(self, profile):
        self.user_profile = profile # the user connected to this client

        self.loginSuccess = Deferred()
        self.loginSuccess.addCallback(profile._loginSuccess)

        self.uokey = None

        self.serv_id = None
        self.room_list = ''
        self.nicks = {}
        self.user_info = {}

    def connectionMade(self):
        self.auth = OnetAuth(self.user_profile.account, self.user_profile.password)
        self.auth.onAuthorised = self.onAuthorised
        self.auth.authorise()

        print ("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))

    def onAuthorised(self, nickname, password, uokey):
        #print 'onAuthorised', nickname
        self.uokey = uokey
        print uokey
        print ("[authorised at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.register()

    def onAuthKeyRecv(self):
        nick = 'NICK %s' % self.user_profile.account
        self.sendData(nick)
        user = 'USER * %s czat-app.onet.pl :%s' % (self.uokey, self.user_profile.account)
        self.sendData(user)
        auth = "AUTHKEY %s" % self.auth.auth(self.authkey)
        self.sendData(auth)

    def connectionLost(self, reason):
        basic.LineReceiver.connectionLost(self, reason)

    def lineReceived(self, line):
        line = line.decode('ISO-8859-2').encode('UTF-8')
        logger.debug("[recv]: %s" % (line))

        part = line.split(' ', 4)
        if part[0].startswith(':'):
            #Lets get server id
            if part[1] == 'NOTICE' and part[2] == 'Auth':
                self.serv_id = part[0]
            if part[0] == self.serv_id:
                if part[1] in consts.numeric_to_symbolic:
                    packet_id = consts.numeric_to_symbolic[part[1]]
                    print "[recv packet]:", packet_id
                    if packet_id == 'ONETAUTHKEY':
                        self.authkey = part[3][1:]
                        self.onAuthKeyRecv()
                    elif packet_id == 'RPL_WELCOME':
                        self.sendData("PROTOCTL ONETNAMESX")
                        self.loginSuccess.callback(self)
                    elif packet_id == 'RPL_ROOMLIST_START':
                        self.room_list = ''
                    elif packet_id == 'RPL_ROOMLIST_MORE':
                        self.room_list += part[3][1:]+','
                    elif packet_id == 'RPL_ROOMLIST_END':
                        self.room_list = self.room_list
                        self.user_profile.onRoomsRecv(self.room_list)
                    elif packet_id == 'RPL_TOPIC':
                        room_id = part[3]
                        topic = part[4][1:]
                        self.user_profile.onTopicRecv(room_id, topic)
                    elif packet_id == 'RPL_NAMREPLY':
                        print part
                        print part[4]
                        room_id, nicks = part[4].split(' :', 2)
                        try:
                            self.nicks[str(room_id)] = str(self.nicks[str(room_id)]+' '+nicks)
                        except:
                            self.nicks[str(room_id)] = nicks
                    elif packet_id == 'RPL_ENDOFNAMES':
                        room_id = part[3]
                        nicks = self.nicks[room_id]
                        self.user_profile.onNicksRecv(room_id, nicks)
            if part[1] == 'PRIVMSG':
                #:Meia!52087932@2294E8.464015.8C906F.765D3D PRIVMSG #Admin :%Fb:times%adminer przekaza� mu co� ? :x
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]
                room_id = part[2]
                try:
                    msg = part[3]+' '+part[4]
                except:
                    msg = part[3]
                msg = msg[1:]
#                try:
#                    formatting = re.findall("%(.+?)%", msg)[0]
#                    msg = msg[len(formatting)+2:]
#                except:
#                    formatting = None
                formatting = None

                self.user_profile.onMsgRecv(room_id, nick, msg, formatting)
            elif part[1] == 'QUIT':
                #:Hydroxyzine!47450187@3DE379.794AE2.DC10C3.260DFE QUIT :Ping timeout: 121 seconds
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                self.user_profile.onNickQuit(nick)
            elif part[1] == 'JOIN':
                #:BaSzKaX!25901787@F4C727.DA810F.2A0EF1.B54653 JOIN #testy :x,0
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]
                room_id = part[2]
                flags = part[3]

                self.user_profile.onNickJoin(nick, room_id, flags)
            elif part[1] == 'PART':
                #:ona_niesklasyfikowana!25306191@0AD995.23792D.D70710.950B18 PART #testy
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                room_id = part[2]

                self.user_profile.onNickPart(nick, room_id)
            elif part[1] == 'NOTICE':
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                if nick == 'NickServ':
                    packet = part[3][1:]
                    if packet == '111':
                        result = part[4].split(' ', 2)
                        info_nick = result[0]
                        info_key = result[1]
                        info_val = result[2]

                        if info_nick not in self.user_info:
                            self.user_info[str(info_nick)] = {}

                        self.user_info[str(info_nick)][str(info_key)] = info_val[1:]
                    elif packet == '112':
                        result = part[4].split(' :')
                        nick = result[0]

                        self.user_profile.userInfoRecv(nick, self.user_info[str(nick)])
                        del self.user_info[str(nick)]
            elif part[1] == 'MODE':
                #:Merovingian!26269559@jest.piekny.i.uroczy.ma.przesliczne.oczy MODE Merovingian :+b
                #:Merovingian!26269559@2294E8.94913F.2EAEC9.11F26D MODE Merovingian :+b
                #:ankaszo!51613093@F4C727.446F67.966AC9.BAAE26 MODE ankaszo -W
                #:NickServ!service@service.onet MODE scc_test +r
                #:ChanServ!service@service.onet MODE #scc +ips
                #:ChanServ!service@service.onet MODE #scc +o scc_test
                #:ChanServ!service@service.onet MODE #scc +eo *!51976824@* scc_test
                #:ChanServ!service@service.onet MODE #abc123 +il-e 1 *!51976824@*
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                if nick == 'NickServ':
                    info_nick = part[2]
                    info_mode = part[3]

                    self.user_profile.userModeRecv(info_nick, info_mode)
                elif nick == 'ChanServ':
                    pass
                else:
                    if nick == part[2]:
                        info_nick = part[2]
                        info_mode = part[3]
                        if info_mode[0] == ':':
                           info_mode = info_mode[1:]

                        self.user_profile.userModeRecv(info_nick, info_mode)
                    else:
                        pass


        elif part[0] == 'PING':
            self.sendPong()

    def sendData(self, line):
        logger.debug("[send]: %s" % (line))
        self.sendLine(str(line+"\n\r").encode('ISO-8859-2'))

    def register(self):
        self.sendData('AUTHKEY')

    def sendPong(self):
        self.sendData('PONG '+self.serv_id)

    #
    # High-level interface callbacks
    #

    def _warn(self, obj):
        tlog.warning( str(obj) )

    def _log(self, obj):
        tlog.msg( str(obj) )

    def _log_failure(self, failure, *args, **kwargs):
        print "Failure:"
        failure.printTraceback()


class CamProtocol(Protocol):
#[recv]: 231 0 OK kkszysiu2
#[recv]: 232 0 CMODE 0
#[recv]: 264 0 CODE_ACCEPTED ffffffff 2147483647
#[recv]: 233 0 QUALITY_FACTOR 1
#[recv]: 250 10118 OK
#[recv]: dlazdecydowanejnapriv:1::0::0251 118 UPDATE
#[recv]: RRadekk:1:3/0/#SEX_CZAT/0,3/0/#chc�_sexu/0,3/0/#kamera_sex/0,3/0/#BEZ_MAJTECZEK/0,3/0/#Ukryta_kamera/0,3/0/#Bi/0:5::16251 22 UPDATE
#[recv]: lessbijkaaaaa:1::1:4:0251 34 UPDATE
#[recv]: slodka36:0:3/0/#kamera_sex/0:0:0:0251 38 UPDATE
#[recv]: x19kamil88x21:0:3/0/#chc�_sexu/0:0:0:0251 38 UPDATE
#[recv]: x19kamil88x21:0:3/0/#chc�_sexu/0:0:0:0254 1021 USER_COUNT_UPDATE
    def __init__(self, conn, nick, uokey):
        self.conn = conn
        self.nick = nick # the user connected to this client
        self.uokey = uokey
        
        self.packet_id = None
        self.__buffer = ''
        #self.nicks = ['szczupla40']
        self.applet_ver = '3.1(applet)'

        self.__packet_id = None
        self.__packet_data_len = 0
        self.__packet_nick = None
        self.__getting_data = False
        
        self.__img_id = 0

        self.loops = {}

        self.loginSuccess = Deferred()
        self.loginSuccess.addCallback(self.conn._loginSuccess)

    def connectionMade(self):
        self.sendData('CAUTH 1234567890123456 %s' % (self.applet_ver))
        print ("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))

    def onAuthorised(self, nickname, password, uokey):
        #print 'onAuthorised', nickname
        print ("[authorised at %s]" %
                        time.asctime(time.localtime(time.time())))

    def onAuthKeyRecv(self):
        pass

    def connectionLost(self, reason):
        print reason
        #basic.LineReceiver.connectionLost(self, reason)

    #def __pop_data(self, n):
    #    data, self.__buffer = self.__buffer[:n], self.__buffer[n:]
    #    return data

    def dataReceived(self, data):
        self.__buffer += data

        if self.__getting_data == False:
            if self.__buffer:
                packet_id = self.__buffer[:3]
                #print packet_id

                if packet_id == '268':
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1

                    auth = 'AUTH %s %s' % (self.uokey, self.applet_ver)
                    self.sendData(auth)

                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '231' or packet_id == '232' or packet_id == '233' or packet_id == '200':
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1

                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '264':
                    #dont know what it is but looks useful :P
                    #264 0 CODE_ACCEPTED ffffffff 2147483647
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1

                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '250':
                    print 'ok, lets have fun fun fun :P'

                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data

                    packet_data_len = len(packet_data)+1

                    self.__buffer = self.__buffer[packet_data_len:]

                    part = packet_data.split(' ', 3)
                    bytestoget = part[1]

                    self.__packet_id = 250
                    self.__packet_data_len = int(bytestoget)
                    self.__getting_data = True
                elif packet_id == '251':
                    packet_header_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_header_data

                    part = packet_header_data.split(' ', 3)
                    #print part[1]

                    #FIXME: this should be fetched like 250 packet!

                    packet_header_data_len = len(packet_header_data)+1

                    self.__buffer = self.__buffer[packet_header_data_len:]

                    packet_data = self.__buffer[:int(part[1])]
                    print packet_data
                    packet_data_len = len(packet_data)

                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '252' or packet_id == '253':
                    #252 0 USER_STATUS szczupla40
                    #253 0 USER_VOTES szczupla40 0
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1

                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '254':
                    #254 1854 USER_COUNT_UPDATE
                    packet_header_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_header_data
                    packet_header_data_len = len(packet_header_data)+1

                    self.__buffer = self.__buffer[packet_header_data_len:]

                    part = packet_header_data.split(' ', 3)
                    bytestoget = part[1]

                    self.__packet_id = int(packet_id)
                    self.__packet_data_len = int(bytestoget)
                    self.__getting_data = True
                elif packet_id == '202':
                    packet_header_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_header_data
                    packet_header_data_len = len(packet_header_data)+1

                    self.__buffer = self.__buffer[packet_header_data_len:]

                    part = packet_header_data.split(' ', 4)
                    bytestoget = part[1]

                    self.__packet_id = int(packet_id)
                    self.__packet_data_len = int(bytestoget)
                    self.__packet_nick = str(part[3])
                    self.__getting_data = True
                elif packet_id == '412':
                    #412 0 SUBSCRIBE_FAILED olgusia32
                    #wustepuje jak przylaczymy sie do zbut wielu kamerek

                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1

                    part = packet_data.split(' ', 4)
                    nick = part[3]

                    #self.conn.onSubscribeDenied(nick)

                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '413':
                    #413 0 SUBSCRIBE_DENIED aliina
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1
                    
                    part = packet_data.split(' ', 4)
                    nick = part[3]
                    
                    self.conn.onSubscribeDenied(nick)
                    
                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '408':
                    #408 0 NO_SUCH_USER_SUBSCRIBE LenCia
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1
                    
                    part = packet_data.split(' ', 4)
                    nick = part[3]
                    
                    self.conn.onNoSuchUser(nick)
                    
                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == '405':    
                    #405 0 USER_GONE Restonka
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1
                    
                    part = packet_data.split(' ', 4)
                    nick = part[3]
                    
                    self.conn.onUserGone(nick)
                    
                    self.__buffer = self.__buffer[packet_data_len:]
                elif packet_id == 'SET':
                    #well hacky but works ;)
                    packet_data = self.__buffer[:self.__buffer.index('\n')]
                    print packet_data
                    packet_data_len = len(packet_data)+1
                    
                    self.__buffer = self.__buffer[packet_data_len:]
                else:
                    print 'Unknown packet:', repr(packet_id)
                    print 'Captured data:', self.__buffer[:64]
        else:
            buffer_len = len(self.__buffer)
            if buffer_len > self.__packet_data_len:
                print 'success!'
                print buffer_len

                packet_data = self.__buffer[:self.__packet_data_len]

                self.parseData(self.__packet_id, self.__packet_nick, packet_data)

                self.__buffer = self.__buffer[self.__packet_data_len:]

                self.__packet_id = None
                self.__packet_data_len = 0
                self.__getting_data = False
                self.__packet_nick = None
            else:
                pass

    def parseData(self, id, nick, data):
        if id == 250:
            self.loginSuccess.callback(self)
            self.conn.onUserList(data)
        elif id == 254:
            self.conn.onUserCountUpdate(data)
        elif id == 202:
            self.conn.onImgRecv(nick, data)
            self.__img_id += 1
            #logfile = open('imgs/%s_%s.jpg' % (nick, self.__img_id), 'w')
            #logfile.write(data)
            #logfile.close()
            
            #self.keepAliving(nick)

        #print id, data

    def keepAliving(self, nick):
        #FIXME: should be replaced by task loop
        self.sendData('KEEPALIVE_BIG %s' % (nick))
        #reactor.callLater(5.0, self.keepAliving, nick)

    def startPing(self, nick):
        self.loops[nick] = task.LoopingCall(self.keepAliving, nick)
        self.loops[nick].start(1.0)

    def stopPing(self, nick):
        self.loops[nick].stop()

    def sendData(self, line):
        print '[send] '+repr(line.encode('ISO-8859-2'))
        #self.sendLine(str(line).encode('ISO-8859-2'))
        self.transport.write(str(line+"\n\r").encode('ISO-8859-2'))

    #
    # High-level interface callbacks
    #

    def _warn(self, obj):
        tlog.warning( str(obj) )

    def _log(self, obj):
        tlog.msg( str(obj) )

    def _log_failure(self, failure, *args, **kwargs):
        print "Failure:"
        failure.printTraceback()
