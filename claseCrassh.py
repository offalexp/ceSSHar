#!/usr/bin/env python
# coding=utf-8

"""Python script to automate running commands on switches.
    Cisco Remote Automation via Secure Shell... or C.R.A.SSH for short!

.. currentmodule:: crassh
.. moduleauthor:: Nick Bettison - www.linickx.com

.. pasado a clase por Juan Penalba y Jair Hnatiuk @ offal 13/11/2018

"""

# Import libs
import getpass              # Hide Password Entry
import socket               # TCP/Network/Socket
import time                 # Time
import datetime             # Date
import sys                  #
import getopt               # Command line options
import os                   #
import stat                 # File system
import re                   # Regex
import paramiko             # SSH

# I don't care about long line, deal with it ;)
# pylint: disable=C0301


class claseCrassh(object):

    # Global variables
    crassh_version = "2.8"      # Version Control in a Variable
    remote_conn = ""            # Paramiko Remote Connection
    remote_conn_pre = ""        # Paramiko Remote Connection Settings (pre-connect)


    # Python 2 & 3 input compatibility
    # pylint: disable=W0622
    """
    try:
        input = raw_input
    except NameError:
        pass
    """
    def __init__(self):
        return None
    def print_help(self):
        return None
    def send_command(self, command="show ver", hostname="Switch", bail_timeout=60):
        """Sending commands to a switch, router, device, whatever!
            Args:
            command (str):  The Command you wish to run on the device.
            hostname (str): The hostname of the device (*expected in the* ``prompt``).
            bail_timeout (int): How long to wait for ``command`` to finish before giving up.
            Returns:
            str.  A text blob from the device, including line breaks.
            REF: http://blog.timmattison.com/archives/2014/06/25/automating-cisco-switch-interactions/
        """
        # global remote_conn, remote_conn_pre
        # Start with empty var & loop
        output = ""
        keeplooping = True
        # Regex for either config or enable
        regex = '^' + self.hostname[:20] + '(.*)(\ )?#'
        theprompt = re.compile(regex)
        # Time when the command started, prepare for timeout.
        now = int(time.time())
        timeout = now + bail_timeout
        # Send the command
        self.remote_conn.send(command + "\n")
        # loop the output
        while keeplooping:
            # Setup bail timer
            now = int(time.time())
            if now == timeout:
                print("\n Command %s took %s secs to run, bailing!" % (command, str(bail_timeout)))
                output += "crassh bailed on command: " + command
                keeplooping = False
                break
            # update receive buffer whilst waiting for the prompt to come back
            if self.remote_conn.recv_ready():
                output += self.remote_conn.recv(2048).decode('utf-8')
                # Search the output for our prompt
                theoutput = output.splitlines()
                for lines in theoutput:
                    myregmatch = theprompt.search(lines)
                if myregmatch:
                    keeplooping = False
            # print(output)
        return output

    def do_no_harm(self, command):
        """Check Commands for dangerous things
        Args:
        command (str):  The Command you wish to run on the device.
        Returns:
        Nothing
        This function will ``sys.exit()`` if an *evil* command is found
        >>> crassh.do_no_harm("show ver")
        >>>
        So, good commands just pass through with no response... maybe I should oneday make it a True/False kind of thing.
        """
        # Innocent until proven guilty
        harmful = False
        # Regex match each "command"
        if re.match("rel", command):
            harmful = True
            error = "reload"

        if re.match("wr(.*)\ e", command):
            harmful = True
            error = "write erase"

        if re.match("del", command):
            harmful = True
            error = "delete"

        if harmful:
            print("")
            print("Harmful Command found - Aborting!")
            print("  \"%s\" tripped the do no harm sensor => %s" % (command, error))
            print("\n To force the use of dangerous things, use -X")
            self.print_help()
    
    def isgroupreadable(self, filepath):
        """Checks if a file is *Group* readable

        Args:
        filepath (str):  Full path to file

        Returns:
        bool.  True/False

        Example:

        >>> print(str(isgroupreadable("file.txt")))
        True

        REF: http://stackoverflow.com/questions/1861836/checking-file-permissions-in-linux-with-python

        """

        st = os.stat(filepath)
        return bool(st.st_mode & stat.S_IRGRP)

    def isotherreadable(self, filepath):
        """Checks if a file is *Other* readable

        Args:
        filepath (str):  Full path to file

        Returns:
        bool.  True/False

        Example:

        >>> print(str(isotherreadable("file.txt")))
        True

        """

        st = os.stat(filepath)
        return bool(st.st_mode & stat.S_IROTH)

    def readtxtfile(self, filepath):
        """Read lines of a text file into an array
        Each line is stripped of whitepace.

        Args:
        filepath (str):  Full path to file

        Returns:
        array.  Contents of file

        Example:

        >>> print(readtxtfile("./routers.txt"))
        1.1.1.1
        1.1.1.2
        1.1.1.3

        """
        # Check if file exists
        if os.path.isfile(filepath) is False:
            print("Cannot find %s" % filepath)
            sys.exit()
        # setup return array
        txtarray = []
        # open our file
        f = open(filepath, 'r')
        # Loop thru the array
        for line in f:
            # Append each line to array
            txtarray.append(line.strip())
        # Return results
        return txtarray

    # Read a Crassh Authentication File
    def readauthfile(self, filepath):
        """Read C.R.A.SSH Authentication File

        The file format is a simple, one entry per line, colon separated affair::

            username: nick
            password: cisco

        Args:
        filepath (str):  Full path to file

        Returns:
        tuple.  ``username`` and ``password``

        Example:

        >>> username, password = readauthfile("~/.crasshrc")
        >>> print(username)
        nick
        >>> print(password)
        cisco

        """

        # Check if file exists
        if os.path.isfile(filepath) is False:
            print("Cannot find %s" % filepath)
            sys.exit()
        # Open file
        f = open(filepath, 'r')
        # Loop thru the array
        for fline in f:
            thisline = fline.strip().split(":")
            if thisline[0].strip() == "username":
                username = thisline[1].strip()
            if thisline[0].strip() == "password":
                if self.isgroupreadable(filepath):
                    print("** Password not read from %s - file is GROUP readable ** " % filepath)
                else:
                    if self.isotherreadable(filepath):
                        print("** Password not read from %s - file is WORLD readable **"% filepath)
                    else:
                        password = thisline[1].strip()
                        return username, password

    def connect(self, device="127.0.0.1", username="cisco", password="cisco", enable=False, enable_password="cisco", sysexit=False, timeout=10):
        """Connect and get Hostname of Cisco Device

        This function wraps up ``paramiko`` and returns the hostname of the **Cisco** device.
        The function creates two global variables ``remote_conn_pre`` and ``remote_conn`` which
        are the paramiko objects for direct manipulation if necessary.

        Args:
        device (str):  IP Address or Fully Qualifed Domain Name of Device
        username (str): Username for SSH Authentication
        password (str): Password for SSH Authentication
        enable (bool): Is enable going to be needed?
        enable_password (str): The enable password
        sysexit (bool): Should the connecton exit the script on failure?

        Returns:
        str.  The hostname of the device

        Example:
        >>> hostname = connect("10.10.10.10", "nick", "cisco")
        >>> print(hostname)
        r1

        REF:
            * https://pynet.twb-tech.com/blog/python/paramiko-ssh-part1.html
            * http://yenonn.blogspot.co.uk/2013/10/python-in-action-paramiko-handling-ssh.html
        """
        hostname = False
        # Create paramiko object
        self.remote_conn_pre = paramiko.SSHClient()
        # Change default paramiko object settings
        self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # print("Connecting to %s ... " % device)
        try:
            self.remote_conn_pre.connect(
                device, username=username, password=password, allow_agent=False, look_for_keys=False, timeout=timeout)
        except paramiko.AuthenticationException as e:
            print("Authentication Error: %s" % e)
            if sysexit:
                sys.exit()
            return False
        except paramiko.SSHException as e:
            print("SSH Error: %s" % e)
            if sysexit:
                sys.exit()
            return False
        except socket.error as e:
            print("Connection Failed: %s" % e)
            if sysexit:
                sys.exit()
            return False
        except:
            print("Unexpected error:", sys.exc_info()[0])
            if sysexit:
                sys.exit()
            return False

        # Connected! (invoke_shell)
        self.remote_conn = self.remote_conn_pre.invoke_shell()

        # Flush buffer.
        output = self.remote_conn.recv(1000).decode('utf-8')
        del output
        output = ""

        # If we have enable password, send it.
        if enable:
            self.remote_conn.send("enable\n")
            time.sleep(0.5)
            self.remote_conn.send(enable_password + "\n")

        # Disable <-- More --> on Output
        self.remote_conn.sendall("terminal length 0\n")
        time.sleep(0.5)

        while "#" not in output:
            # update receive buffer
            if self.remote_conn.recv_ready():
                output += self.remote_conn.recv(1024).decode('utf-8')
        # Clear the Var.
        del output
        output = ""

        # Ok, let's find the device hostname
        self.remote_conn.sendall("show run | inc hostname \n")
        time.sleep(0.5)

        keeplooping = True
        while keeplooping:
            if self.remote_conn.recv_ready():
                output += self.remote_conn.recv(1024).decode('utf-8')
                for subline in output.splitlines():
                    if re.match("^hostname", subline):
                        #print("Match %s" % subline)
                        thisrow = subline.split()
                        try:
                            gotdata = thisrow[1]
                            if thisrow[0] == "hostname":
                                hostname = thisrow[1]
                                #prompt = hostname + "#"
                        except IndexError:
                            gotdata = 'null'
                        keeplooping = False
        # Catch looping failures.
        if hostname is False:
            print("Hostname Lookup Failed: \n %s \n" % output)
            if sysexit:
                sys.exit()
        else:
            self.hostname = hostname
        # Found it! Return it!
        return hostname

    def disconnect(self):
        """Disconnect an SSH Session
        Crassh wrapper for paramiko disconnect
        No Arguments, disconnects the current global variable ``remote_conn_pre``
        """
        self.remote_conn_pre.close()

    def main(self):
        """Main Code Block
        This is the main script that Network Administrators will run.
        No Argumanets. Input is used for missing CLI Switches.
        """
        # import Global Vars
        global input

        # Main Vars (local scope)
        switches = [] # Switches, devices, routers, whatever!
        commands = []
        filenames = []
        sfile = '' # Switch File
        cfile = '' # Command File

        # Default variables (values)
        play_safe = True
        enable = False
        delay_command = False
        writeo = True
        printo = False
        bail_timeout = 60
        connect_timeout = 10
        sysexit = True
        backup_credz = False
        backup_enable = False

        # Default Authentication File Path
        crasshrc = os.path.expanduser("~") + "/.crasshrc"

        # Get script options - http://www.cyberciti.biz/faq/python-command-line-arguments-argv-example/
        try:
            myopts, args = getopt.getopt(sys.argv[1:], "c:s:t:T:d:A:U:P:B:b:E:hpwXeQ")
        except getopt.GetoptError as e:
            print("\n ERROR: %s" % str(e))
            self.print_help()

        for o, a in myopts:
            if o == '-s':
                sfile = a
                switches = self.readtxtfile(sfile)

            if o == '-c':
                cfile = a
                commands = self.readtxtfile(cfile)

            if o == '-t':
                bail_timeout = int(a)

            if o == '-T':
                connect_timeout = int(a)

            if o == '-h':
                print("\n Nick\'s Cisco Remote Automation via Secure Shell- Script, or C.R.A.SSH for short!")
                self.print_help()

            if o == '-p':
                writeo = False
                printo = True

            if o == '-w':
                writeo = True

            if o == '-X':
                play_safe = False

            if o == '-Q':
                sysexit = False

            if o == '-e':
                enable = True

            if o == '-d':
                delay_command = True
                delay_command_time = int(a)

            if o == '-A':
                crasshrc = str(a)

            if o == '-U':
                username = str(a)

            if o == '-P':
                password = str(a)

            if o == '-B':
                backup_credz = True
                backup_username = str(a)

            if o == '-b':
                backup_credz = True
                backup_password = str(a)

            if o == '-E':
                backup_enable = True
                backup_enable_password = str(a)

        # See if we have an Authentication File
        if os.path.isfile(crasshrc) is True:
            try:
                username, password = readauthfile(crasshrc)
            except:
                pass

        # Do we have any switches?
        if sfile == "":
            try:
                iswitch = input("Enter the switch to connect to: ")
                switches.append(iswitch)
            except:
                sys.exit()

        # Do we have any commands?
        if cfile == "":
            try:
                icommand = input("The switch command you want to run: ")
                commands.append(icommand)
            except:
                sys.exit()

        """
            Check the commands are safe
        """
        if play_safe:
            for command in commands:
                self.do_no_harm(command)
        else:
            print("\n--\n Do no Harm checking DISABLED! \n--\n")

        """
            Capture Switch log in credentials...
        """

        try:
            username
        except:
            try:
                username = input("Enter your username: ")
            except:
                sys.exit()

        try:
            password
        except:
            try:
                password = getpass.getpass("Enter your password:")
            except:
                sys.exit()

        if enable:
            try:
                enable_password = getpass.getpass("Enable password:")
            except:
                sys.exit()

        if backup_credz:
            try:
                backup_password
            except:
                try:
                    backup_password = getpass.getpass("Enter your backup SSH password:")
                except:
                    sys.exit()
        """
            Time estimations for those delaying commands
        """
        if delay_command:
            time_estimate = datetime.timedelta(0, (len(commands) * (len(switches) * 2) * delay_command_time)) + datetime.datetime.now()
            print(" Start Time: %s" % datetime.datetime.now().strftime("%H:%M:%S (%y-%m-%d)"))
            print(" Estimatated Completion Time: %s" % time_estimate.strftime("%H:%M:%S (%y-%m-%d)"))

        """
            Progress calculations - for big jobs only
        """
        if (len(commands) * len(switches)) > 100:
            counter = 0

        """
            Ready to loop thru switches
        """

        for switch in switches:

            if backup_credz:
                tmp_sysexit = sysexit # re-assign so, don't bail on authentication failure
                sysexit = False

            if enable:
                hostname = self.connect(switch, username, password, enable, enable_password, sysexit, connect_timeout)
            else:
                hostname = self.connect(switch, username, password, False, "", sysexit, connect_timeout)

            if isinstance(hostname, bool): # Connection failed, function returned False
                if backup_credz:
                    sysexit = tmp_sysexit # put it back, so fail or not (-Q) works as expected on backup credz
                    print("Trying backup credentials")
                    if backup_enable:
                        hostname = self.connect(switch, backup_username, backup_password, enable, backup_enable_password, sysexit, connect_timeout)
                    else:
                        hostname = self.connect(switch, backup_username, backup_password, False, "", sysexit, connect_timeout)

                    if isinstance(hostname, bool): # Connection failed, function returned False
                        continue
                else:
                    continue

            # Write the output to a file (optional) - prepare file + filename before CMD loop
            if writeo:
                filetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
                filename = hostname + "-" + filetime + ".txt"
                filenames.append(filename)
                f = open(filename, 'a')

            # Command Loop
            for cmd in commands:

                # Send the Command
                print("%s: Running: %s" % (hostname, cmd))
                output = self.send_command(cmd, hostname, bail_timeout)

                # Print the output (optional)
                if printo:
                    print(output)
                if writeo:
                    f.write(output)

                # delay next command (optional)
                if delay_command:
                    time.sleep(delay_command_time)

                # Print progress
                try:
                    counter
                    # Random calculation to find 10 percent
                    if (counter % 10) == 0:
                        completion = ((float(counter) / (float(len(commands)) * float(len(switches)))) * 100)
                        if int(completion) > 9:
                            print("\n  %s%% Complete" % int(completion))
                            if delay_command:
                                time_left = datetime.timedelta(0, (((int(len(commands)) * int(len(switches))) + (len(switches) * 0.5)) - counter)) + datetime.datetime.now()
                                print("  Estimatated Completion Time: %s" % time_left.strftime("%H:%M:%S (%y-%m-%d)"))
                            print(" ")
                    counter += 1
                except:
                    pass


            # /end Command Loop

            if writeo:
                # Close the File
                f.close()


            # Disconnect from SSH
            self.disconnect()

            if writeo:
                print("Switch %s done, output: %s" % (switch, filename))
            else:
                print("Switch %s done" % switch)

            # Sleep between SSH connections
            time.sleep(1)

        print("\n") # Random line break

        print(" ********************************** ")
        if writeo:
            print("  Output files: ")

            for ofile in filenames:
                print("   - %s" % ofile)

            print(" ---------------------------------- ")
        print(" Script FINISHED ! ")
        if delay_command:
            print(" Finish Time: %s" % datetime.datetime.now().strftime("%H:%M:%S (%y-%m-%d)"))
        print(" ********************************** ")
