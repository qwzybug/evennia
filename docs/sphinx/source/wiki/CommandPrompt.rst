Adding a command prompt
=======================

A *prompt* is quite common in MUDs. The prompt display useful details
about your character that you are likely to want to keep tabs on at all
times, such as health, magical power etc. It might also show things like
in-game time, weather and so on.

Prompt after the command
------------------------

One common form of prompt appears after every command you send. So, say
you enter the look command; you would then get the result of the look
command, followed by the prompt. As an example:Â 

::

      > look
    You see nothing special.
    HP:10, SP:20, MP: 5 

MUD clients can be set to detect prompts like this and display them in
various client-specific ways.

To add this kind of "after-every-command-prompt", you can use the
``at_post_cmd()`` hook. This is to be defined on the Command class and
Evennia will always call it right after ``func()`` has finished
executing. For this to appear after every command you enter, it's best
to put this in the parent for your own commands. You can also put it
only in certain commands (might not be too useful to show it if you are
doing game administration for example).

::

    class MyCommand(Command):

        [...]

        def at_post_cmd(self):
        
            # we assume health/stamina/magic are just stored
            # as simple attributes on the character. 

            hp = self.caller.db.hp
            sp = self.caller.db.sp
            mp = self.caller.db.mp

            self.caller.msg("HP: %i, SP: %i, MP: %i" % (hp, sp, mp))

Note that if you are using the default commands, they will *not* display
a command prompt after this change - they are inheriting from
``src.commands.default.muxcommand.MuxCommand``. If you want to modify
default commands you need to copy&paste the default command definitions
to ``game/gamesrc/commands`` and modify them so they inherit from your
new parent (and re-point Evennia to use your custom versions as
described `here <AddingCommandTutorial.html>`_). If you only want to add
the hook and don't need to change anything else you can just create
stubs in modules in ``game/gamesrc/commands`` on this form:

::

    from ev import default_cmds
    from game.gamesrc.commands.basecommand import MyCommand

    class CmdLook(MyCommand, default_cmds.CmdLook):
        pass

    class CmdGet(MyCommand, default_cmds.CmdGet):
        pass

This multiple inheritance should make use of your custom ``at_post_cmd``
hook while otherwise using the default command's code. This type of
overload is useful not only for adding prompts but for many different
forms of overloading default functionality.

Prompt on the same line
-----------------------

Another, more advanced type of prompt is one that appears before the
return of every command, on the same line:

::

      > look
    HP: 10, SP:20, MP:5 -- You see nothing special.

Now, there is an ``at_pre_cmd()`` hook analogous to the hook from last
section except called just *before* parsing of the command. But putting
prompt code in that would just have the prompt appear on the *line
before* the function return:

::

      > look
    HP:10, SP:20, MP: 5 
    You see nothing special.

... which might be cool too, but is not what we wanted. To have the
prompt appear on the same line as the return, we need to change how
messages are returned to the player. This means a slight modification to
our *Character typeclass* (see [Objects#Characters here] on how to
change the default Character class to your custom one).

All in-game commands use the ``object.msg()`` method for communicating
with the player (this is usually called as ``self.caller.msg()`` inside
command classes). This method is defined in ``src/objects/models.py``,
on the ``ObjectDB`` base class. This is the signature of ``msg()``
method:

::

    def msg(self, outgoing_message, from_obj=None, data=None): 
       ...

The only argument we are interested in here is the ``outgoing_message``,
which contains the text that is about to be passed on to the player. We
want to make sure that ``msg()`` always tack our prompt in front of the
``outgoing_message`` before sending it on. This is done by simply
overloading the ``msg()`` method in our custom Character class. On your
custom Character typeclass add this:

::

    def msg(self, outgoing_message, from_obj=None, data=None):  
     
        # prepend the prompt in front of the message

        hp = self.db.hp
        sp = self.db.sp
        mp = self.db.mp 
        prompt = "%i, %i, %i -- " % (hp, sp, mp)
        outgoing_message = prompt + outgoing_message

        # pass this on to the original msg() method on the database object

        self.dbobj.msg(outgoing_message, from_obj=from_obj, data=data)    

Note that this solution will *always* give you the prompt, also if you
use admin commands, which could get annoying. You might want to have
some attribute defined on your character for turning on/off the prompt
(the msg() method could look for it to determine if it should add the
prompt or not). You can of course also name the above method
``msg_prompt()`` and make sure that only commands that *should* return a
prompt call that method.
