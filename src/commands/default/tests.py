# -*- coding: utf-8 -*-
"""
 ** OBS - this is not a normal command module! **
 ** You cannot import anything in this module as a command! **

This is part of the Evennia unittest framework, for testing the
stability and integrity of the codebase during updates. This module
test the default command set. It is instantiated by the
src/objects/tests.py module, which in turn is run by as part of the
main test suite started with
 > python game/manage.py test.

"""

import re, time
try:
    # this is a special optimized Django version, only available in current Django devel
    from django.utils.unittest import TestCase
except ImportError:
    from django.test import TestCase
from django.conf import settings
from src.utils import create 
from src.server import session, sessionhandler
from src.config.models import ConfigValue

#------------------------------------------------------------ 
# Command testing 
# ------------------------------------------------------------

# print all feedback from test commands (can become very verbose!)
VERBOSE = False

class FakeSession(session.Session): 
    """ 
    A fake session that
    implements dummy versions of the real thing; this is needed to
    mimic a logged-in player.  
    """ 
    protocol_key = "TestProtocol"
    def connectionMade(self):
        self.session_connect('0,0,0,0')     
    def disconnectClient(self): 
        pass 
    def lineReceived(self, raw_string): 
        pass 
    def msg(self, message, data=None):             
        if message.startswith("Traceback (most recent call last):"):
            #retval = "Traceback last line: %s" % message.split('\n')[-4:]
            raise AssertionError(message)
        if self.player.character.ndb.return_string != None:
            return_list = self.player.character.ndb.return_string
            if hasattr(return_list, '__iter__'):
                rstring = return_list.pop(0)
                self.player.character.ndb.return_string = return_list
            else:
                rstring = return_list
                self.player.character.ndb.return_string = None
            if not message.startswith(rstring):
                retval = "Returned message ('%s') != desired message ('%s')" % (message, rstring)
                raise AssertionError(retval)
        if VERBOSE:
            print message

class CommandTest(TestCase):
    """
    Sets up the basics of testing the default commands and the generic things
    that should always be present in a command.

    Inherit new tests from this.
    """
    def setUp(self):
        "sets up the testing environment"                
        c = ConfigValue(db_key="default_home", db_value="2")
        c.save()

        self.room1 = create.create_object(settings.BASE_ROOM_TYPECLASS, key="room1")
        self.room2 = create.create_object(settings.BASE_ROOM_TYPECLASS, key="room2")

        # create a faux player/character for testing.
        self.char1 = create.create_player("TestingPlayer", "testplayer@test.com", "testpassword", location=self.room1)
        self.char1.player.user.is_superuser = True
        self.char1.ndb.return_string = None
        sess = FakeSession()
        sess.connectionMade()
        sess.session_login(self.char1.player)
        # create second player and some objects 
        self.char2 = create.create_object(settings.BASE_CHARACTER_TYPECLASS, key="char2", location=self.room1)
        self.char2.ndb.return_string = None
        self.obj1 = create.create_object(settings.BASE_OBJECT_TYPECLASS, key="obj1", location=self.room1)
        self.obj2 = create.create_object(settings.BASE_OBJECT_TYPECLASS, key="obj2", location=self.room1)
        self.exit1 = create.create_object(settings.BASE_EXIT_TYPECLASS, key="exit1", location=self.room1)
        self.exit2 = create.create_object(settings.BASE_EXIT_TYPECLASS, key="exit2", location=self.room2)        
        
    def get_cmd(self, cmd_class, argument_string=""):
        """
        Obtain a cmd instance from a class and an input string
        Note: This does not make use of the cmdhandler functionality.
        """        
        cmd = cmd_class()
        cmd.caller = self.char1
        cmd.cmdstring = cmd_class.key
        cmd.args = argument_string
        cmd.cmdset = None
        cmd.obj = self.char1
        return cmd
    
    def execute_cmd(self, raw_string, wanted_return_string=None):
        """
        Creates the command through faking a normal command call; 
        This also mangles the input in various ways to test if the command
        will be fooled.
        """ 
        if not VERBOSE:
            # only mangle if not VERBOSE, to make fewer return lines
            test1 = re.sub(r'\s', '', raw_string) # remove all whitespace inside it
            test2 = "%s/åäö öäö;-:$£@*~^' 'test" % raw_string # inserting weird characters in call
            test3 = "%s %s" % (raw_string, raw_string) # multiple calls 
            self.char1.execute_cmd(test1)
            self.char1.execute_cmd(test2)
            self.char1.execute_cmd(test3)
        # actual call, we potentially check so return is ok. 
        self.char1.ndb.return_string = wanted_return_string
        try:
            self.char1.execute_cmd(raw_string)
        except AssertionError, e:
            self.fail(e)
        self.char1.ndb.return_string = None
#------------------------------------------------------------
# Default set Command testing
#------------------------------------------------------------

class TestHome(CommandTest):
    def test_call(self):
        self.char1.location = self.room1
        self.char1.home = self.room2
        self.execute_cmd("home")
        self.assertEqual(self.char1.location, self.room2)
class TestLook(CommandTest):
    def test_call(self):
        self.execute_cmd("look here")
class TestPassword(CommandTest):
    def test_call(self):
        self.execute_cmd("@password testpassword = newpassword")
class TestNick(CommandTest):
    def test_call(self):
        self.execute_cmd("nickname testalias = testaliasedstring")        
        self.assertEquals("testaliasedstring", self.char1.nicks.get("testalias", None))

# system.py command tests
class TestPy(CommandTest):
    def test_call(self):
        self.execute_cmd("@py 1+2", [">>> 1+2", "<<< 3"])
class TestListScripts(CommandTest):
    def test_call(self):
        self.execute_cmd("@scripts")
class TestListObjects(CommandTest):
    def test_call(self):
        self.execute_cmd("@objects")
class TestListService(CommandTest):
    def test_call(self):
        self.execute_cmd("@service")
class TestVersion(CommandTest):
    def test_call(self):
        self.execute_cmd("@version")
class TestTime(CommandTest):
    def test_call(self):
        self.execute_cmd("@time")
class TestList(CommandTest):
    def test_call(self):
        self.execute_cmd("@list")
class TestPs(CommandTest):
    def test_call(self):
        self.execute_cmd("@ps","\n{wNon-timed scripts")
class TestStats(CommandTest):
    def test_call(self):
        self.execute_cmd("@stats")