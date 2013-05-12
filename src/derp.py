#!/usr/bin/env python
#
# DERP- Device Environment Replacement Program
# Copyright (C) 2013 fattire <f4ttire@gmail.com> (not the beer!)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

import sys
import os
import platform
import xml.etree.ElementTree as ET
from threading import Thread

if sys.version_info < (2, 7):
    print "This program requires python version 2.7 or higher."
    sys.exit(1)

try:
    import wx.html
except ImportError:
    print '''This program requires wxpython.  On Debian-based Linux, including
    Ubuntu and Mint, you can install it with the following command:\n\n
    sudo apt-get install python-wxgtk2.8\n'''
    sys.exit(1)

if wx.MAJOR_VERSION == 2:
    if wx.MINOR_VERSION < 9 and platform.system() == "Darwin":
        print "The Mac needs at least wxWidgets version 2.9 (cocoa).  Sorry."
        exit(1)

# CONSTANTS & PLATFORM STUFF

app_name = "DERP"
app_version = "0.001"
scriptFolder = os.path.dirname(os.path.realpath(__file__)) + "/../scripts/"
home = os.path.expanduser("~")

if platform.system() == "Darwin":
    androidSdk = ["http://dl.google.com/android/",
                  "android-sdk_r21.1-macosx.zip",
                  "ac2dc476c14ae60e85bc2d889cdab0ff17992891e0ed9107e651aaa86c18a1d3ff9df81fd6bd35c01b26010484fd67a84915f157749bce7a061c7fe4b789c405",
                  "android-sdk-macosx/"]
    toolsFolder = "/Library/Application Support/" + app_name + "/tools/"
    downloadsFolder = "/Library/Application Support/" + app_name + \
                      "/downloads/"
elif platform.system() == "Linux":
    androidSdk = ["http://dl.google.com/android/",
                  "android-sdk_r21.1-linux.tgz",
                  "160cd51f965a23120cf63abe02b9a9ce8913d1239a848bc423b33ad10eff65b30147c6b11ab751aa12154292ce0a7837aa60def1cd31a2ccb5d4fc6fcb6d2c24",
                  "android-sdk-linux/"]
    toolsFolder = "/opt/" + app_name.lower() + "/tools/"
    downloadsFolder = "/tmp/" + app_name.lower() + "/downloads/"
    udevRules = ["/etc/udev/rules.d/", "99-android.rules"]

bash = "/bin/bash"
python = sys.executable

licenseFile = os.path.dirname(os.path.realpath(__file__)) + "/../LICENSE"
welcomeScript = scriptFolder + "derp/welcome/welcome.derp"
tutorialScript = scriptFolder + "derp/tutorial/tutorial.derp"
faqScript = scriptFolder + "derp/faq/faq.derp"

sectionbgcolor = "#E8E8E8" if platform.system() == "Darwin" else "#E0E0E0"
infobgcolor = "#FFFFFF"

EVT_SUBPROCESS_DONE = wx.NewId()


class SubProcessDoneEvt(wx.PyEvent):
    def __init__(self, returnCode):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SUBPROCESS_DONE)
        self.returnCode = returnCode


class SubProcessThread(Thread):

    def __init__(self, args, cwd, notify):
        Thread.__init__(self)
        self.args = args
        self.notify = notify
        self.cwd = cwd
        self.start()
        self.p = None

    def run(self):
        import subprocess
        self.p = subprocess.Popen(self.args, stderr=subprocess.PIPE,
                     stdout=subprocess.PIPE, cwd=self.cwd)
        self.p.wait()
        wx.PostEvent(self.notify, SubProcessDoneEvt(self.p))

    def OnQuit(self, e):
        self.Destroy()


class LicenseFrame (wx.Frame):

    def __init__(self, parent, text):
        dw, dh = wx.DisplaySize()
        wx.Frame.__init__(self, parent, title="License Info", size=(int(dw *0.8), int(dh * 0.8)))
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.control.SetFont(wx.Font(family=wx.FONTFAMILY_TELETYPE,
                             pointSize=12, style=wx.FONTSTYLE_NORMAL,
                             weight=wx.FONTWEIGHT_NORMAL))
        self.control.SetValue(text)
        self.Centre()

    def OnQuit(self, e):
        self.Destroy()


class Console (wx.Frame):

    def __init__(self, parent, title, text):
        dw, dh = wx.DisplaySize()
        wx.Frame.__init__(self, parent, title="Console", size=(int(dw * 0.8), int(dh * 0.8)))
        #define the console
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.control.SetFont(wx.Font(family=wx.FONTFAMILY_TELETYPE,
                             pointSize=12, style=wx.FONTSTYLE_NORMAL,
                             weight=wx.FONTWEIGHT_NORMAL))
        self.UpdateLog(text)
        self.Centre()
#       Green's not working for mac, so comment out for now.
#       self.control.SetBackgroundColour("black")
#       self.control.SetForegroundColour("green")

    def UpdateLog(self, text):
        self.control.SetValue(text)
        self.LineDown()
        self.control.ShowPosition(self.control.GetLastPosition())

    def OnQuit(self, e):
        self.Destroy()


class MainWindow (wx.Frame):

    def __init__(self, parent, title):
        dw, dh = wx.DisplaySize()
        wx.Frame.__init__(self, parent, title=title, size=(int(dw * 0.8), int(dh * 0.8)))

        self.parent = parent

        #create menubar, menus & bindings
        menuBar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        self.editMenu = wx.Menu()
        self.viewMenu = wx.Menu()
        self.helpMenu = wx.Menu()

        self.openItem = self.fileMenu.Append(wx.ID_OPEN, "&Open Script",
                                            "Open Script")
        self.fileMenu.Enable(wx.ID_OPEN, False)
        self.consoleItem = self.viewMenu.Append(wx.ID_ANY, "&Console",
                                                "Console")
        self.debugItem = self.editMenu.AppendCheckItem(wx.ID_ANY, \
                                                       "&Debug Mode",
                                                        "Debug Mode")
        aboutItem = self.helpMenu.Append(wx.ID_ABOUT, "&About " + \
                                         app_name, "About " + app_name)
        self.tutorialItem = self.helpMenu.Append(wx.ID_ANY, \
                                                  "&Script Tutorial",
                                                   "Script Tutorial")
        self.FAQItem = self.helpMenu.Append(wx.ID_ANY, "&FAQ", "View FAQ")
        self.licenseItem = self.viewMenu.Append(wx.ID_ANY, "&License",
                                                "View License")

        self.fileMenu.AppendSeparator()
        self.quitItem = self.fileMenu.Append(wx.ID_EXIT, "&Exit", "Exit")
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

        # add menu items to bar & show
        menuBar.Append(self.fileMenu, "File")
        menuBar.Append(self.editMenu, "Edit")
        menuBar.Append(self.viewMenu, "View")
        menuBar.Append(self.helpMenu, "&Help")
        self.SetMenuBar(menuBar)

        # create boxes
        self.mainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.sectionBox = wx.BoxSizer(wx.HORIZONTAL)
        self.infoBox = wx.BoxSizer(wx.VERTICAL)
        buttonBox = wx.BoxSizer(wx.HORIZONTAL)

        # create panels
        bottomPanel = wx.Panel(self, -1)
        statusPanel = wx.Panel(self, -1)
        self.statusText = wx.StaticText(statusPanel, label="Debug Mode: On")
        self.statusText.SetForegroundColour("green")

        # create HTML areas.
        self.infoHtml = wx.html.HtmlWindow(self)
        self.titleHtml = wx.html.HtmlWindow(self,
                                            style=wx.html.HW_SCROLLBAR_NEVER)
        self.sectionHtml = wx.html.HtmlWindow(self)

        # fill buttonbox
        bottomPanel.SetBackgroundColour(sectionbgcolor)
        self.statusText.SetBackgroundColour(sectionbgcolor)
        statusPanel.SetBackgroundColour(sectionbgcolor)
        self.nextBtn = wx.Button(bottomPanel, wx.ID_FORWARD, size=(-1, 23),
                                 label='Continue')
        buttonBox.Add(statusPanel, 2, flag=wx.EXPAND)
        buttonBox.AddStretchSpacer(4)
        buttonBox.Add(bottomPanel, 0, flag=wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND)
        buttonBox.AddStretchSpacer(1)
        self.SetBackgroundColour(sectionbgcolor)
        self.nextBtn.SetFocus()

        #progress bar
        self.activityBar = wx.Gauge(self, wx.ID_ANY)
        self.activityBar.Hide()

        # fill infobox
        self.infoBox.AddStretchSpacer(1)
        self.infoBox.Add(self.titleHtml, 3, wx.EXPAND)
        self.infoBox.Add(self.infoHtml, 20, wx.EXPAND)
        self.infoBox.Add(self.activityBar, 1, wx.EXPAND)
        self.infoBox.AddStretchSpacer(1)
        self.infoBox.Add(buttonBox, 0, wx.EXPAND)
        self.infoBox.AddStretchSpacer(1)
        # fill sectionbox
        self.sectionBox.Add(self.sectionHtml, 1, flag=wx.EXPAND)

        # now fill mainbox
        self.mainBox.Add(self.sectionBox, 10, wx.EXPAND)
        self.mainBox.Add(self.infoBox, 26, wx.EXPAND)
        self.mainBox.AddStretchSpacer(1)

        self.Centre()
        self.SetSizer(self.mainBox)
        self.SetAutoLayout(True)
        self.Layout()
        # don't let window get smaller than it is now
        self.SetMinSize(self.GetSize())
        self.Show(True)

    def setInfoTitle(self, text):
        self.titleHtml.SetPage('<BODY BGCOLOR="' + infobgcolor + \
                               '"><center><font size="+4">' + text + \
                               "</font></center></BODY>")

    def setSection(self, text):
        self.sectionHtml.SetPage('<BODY BGCOLOR="' + sectionbgcolor + '">' \
                                 + text + "</BODY>")

    def setInfo(self, text):
        self.infoHtml.SetPage('<font size="+1">' + text + "</font>")

    def OnAbout(self, event):
        info = wx.AboutDialogInfo()
        info.SetName(app_name)
        info.SetDescription("A cross-platform installer for " + \
                            "Android mobile devices (and more).")
        info.SetVersion(app_version)
        info.AddDeveloper('fattire')
        info.SetCopyright('(C) 2013 The developers of this program')
        info.SetLicence('The GNU Public License, Version 2')
        wx.AboutBox(info)

    def OnOpen(self, event):
        dlg = wx.FileDialog(self, "Choose a DERP installation script",
                            scriptFolder, "(*.derp)|*.derp", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetPath()
        return False

    def OnQuit(self, event):
        self.Destroy()

    def Notify(self, text):
        wx.MessageBox(text, "Attention", wx.OK)


class Script():

    def __init__(self):

        self.currentStep = 0
        self.currentSection = 0
        self.log = ""
        self.frame = MainWindow(None, app_name)
        self.frame.EnableCloseButton(False)
        self.console = Console(None, "Console", self.log)
        self.ScriptLog("-----Welcome to The DERP Installer!-----")
        self.subprocessRunning = False
        self.updatedTools = False

        self.LoadScriptFromFile(welcomeScript)

        self.frame.Bind(wx.EVT_MENU, self.OnQuit, self.frame.quitItem)
        self.frame.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.frame.Bind(wx.EVT_BUTTON, self.OnNext, self.frame.nextBtn)
        self.frame.Bind(wx.EVT_MENU, self.OnOpen, self.frame.openItem)
        self.frame.Bind(wx.EVT_MENU, self.OnDebug, self.frame.debugItem)
        self.frame.Bind(wx.EVT_MENU, self.OnConsole, self.frame.consoleItem)
        self.frame.Bind(wx.EVT_MENU, self.OnFaq, self.frame.FAQItem)
        self.frame.Bind(wx.EVT_MENU, self.OnLicense, self.frame.licenseItem)
        self.frame.Bind(wx.EVT_MENU, self.OnTutorial, self.frame.tutorialItem)

        # make tools/downloads directories
        if not os.path.exists(toolsFolder):
            os.makedirs(toolsFolder)
        if not os.path.exists(downloadsFolder):
            os.makedirs(downloadsFolder)

        # Change the line below to make debug ON by default.
        self.frame.debugItem.Check(False)
        self.OnDebug(-1)

        # when spawned process returns, let us know.
        self.frame.Connect(-1, -1, EVT_SUBPROCESS_DONE, self.EndSubProcess)

    def OnTutorial(self, e):
        if wx.MessageBox("Replace any currently-running script " + \
                         "with script-writing tips?",
                         "Tutorial?",
                        wx.YES_NO | wx.NO_DEFAULT) == wx.YES:
            self.LoadScriptFromFile(tutorialScript)

    def OnConsoleClose(self, e):
        # intercept closing the console to hide, not kill
        self.OnConsole(e)
        e.Veto()

    def OnFaq(self, e):
        if wx.MessageBox("Replace any currently-running script with the FAQ?",
                         "Frequently Asked Questions?",
        wx.YES_NO | wx.NO_DEFAULT) == wx.YES:
            self.LoadScriptFromFile(faqScript)

    def OnLicense(self, e):
        try:
            with open(licenseFile, "r") as licfile:
                text = licfile.read()
        except:
            self.frame.Notify("Error reading license file: " + license)
        try:
            self.license.Show()
            self.license.Raise()
        except:
            self.license = LicenseFrame(None, text)
            self.license.Show()

    def OnConsole(self, e):
        try:
            self.console.Show(not self.console.IsShown())
            self.console.Raise()
        except:
            #console was closed, so recreate it
            self.console = Console(None, "Console", self.log)
            self.console.Show(not self.console.IsShown())

    def OnDebug(self, e):
        self.debug = self.frame.debugItem.IsChecked()
        self.frame.statusText.SetLabel("Debug Mode: " + ("On" if self.debug \
                                                         else "Off"))
        self.frame.statusText.SetOwnForegroundColour("green" if self.debug \
                                                     else "red")
        self.ScriptLog("Debug Mode set to: " + str(self.debug))

    def OnOpen(self, e):
        filename = self.frame.OnOpen(e)
        if (filename):
            self.LoadScriptFromFile(filename)

    def OnNext(self, e):
        self.RunScript()

    def OnQuit(self, e):
        if wx.MessageBox("You sure you want to quit " + app_name + \
                        "?  This will stop any currently-running script.",
                        "Quit?",
                        wx.YES_NO | wx.NO_DEFAULT) == wx.YES:
            self.ScriptLog("Quitting...")
            self.frame.OnQuit(e)
            try:
                if self.console:
                    self.console.OnQuit(e)
                if self.license:
                    self.license.OnQuit(e)
                # (Any subprocess will have to quit on its own,
                #  unless there's a way to force quit it.)
            except:
                pass
            sys.exit(0)

    def LoadScriptFromFile(self, filename):
        try:
            self.thisScript = ET.parse(filename).getroot()
        except Exception as e:
            self.ScriptLog("ERROR:  Couldn't parse " + filename)
            self.frame.Notify("There was an error parsing: " + filename + \
                              " :\n\n" + repr(e) + "\n\nCheck to make "
                              "sure it's valid XML and try again.")
        if self.IsScript():
            self.currentStep = 0
            self.currentSection = 0
            self.ReadSections()
            self.ScriptLog("-----Starting New Script:  " + filename + "-----")
            self.RunScript()
            self.frame.nextBtn.SetLabel("Continue")
            self.frame.nextBtn.Enable()
            self.frame.nextBtn.SetFocus()

    def IsScript(self):
        if self.thisScript.tag.lower() != app_name.lower():
            self.ScriptLog("BAD SCRIPT:  This does not appear to be a " \
                            + app_name + " XML Script.")
            self.frame.Notify("This does not appear to be a " + app_name + \
                              " XML Script.")
            return False
        if self.thisScript.get("app_version") != app_version:
            self.ScriptLog("BAD SCRIPT: Unsupported version.  Wanted '" + \
                            app_version + "'.")
            self.frame.Notify("This is an " + app_name + \
                              " XML Script, but it's for another version.")
            return False
        if self.thisScript.get("os") != None and \
                self.thisScript.get("os").count(platform.system()) == 0:
            self.ScriptLog("BAD SCRIPT:  This script is not meant " + \
                           "to be run on this operating system.")
            self.frame.Notify("This is a " + app_name + " script, but " + \
                              "it's meant for another operating system.")
            return False

        actions = self.thisScript.iter("action")
        sawWarning = False
        for action in actions:
            if action.get("type") == "bash" and action.get("os") == None \
                and sawWarning == False:
                self.ScriptLog(
            "Warning: bash scripts exist without specifying operating system.")
                self.frame.Notify(
      """Warning:  This script contains bash scripts without specifying """ + \
      """ the operating system (via the "os" attribute).\n\nThis is """ + \
      """ discouraged, as the script will run on ALL operating systems """ + \
      """(some of which may not actually support bash).  The script will """ +\
      """now start.  This notice was just a warning.""")
                sawWarning = True
        return True

    def ScriptLog(self, text):
        print app_name + ": " + text
        self.log += text.decode('utf-8') + "\n"
        if self.console:
            self.console.UpdateLog(self.log)

    def BuildSectionList(self):

        title = self.thisScript.get("title")
        if title == None:
            title = ""
        else:
            title += "<br>"
        text = "<br><br><center><font size='+2'><b>" + title + \
               "</b></font></b></center><center><b>Sections</b>" + \
               "</center><hr width=80%><br><ul>"
        for line in self.sections:
            text += "<li> "
            if self.thisScript[self.currentSection].get("name") != None:
                sectionName = self.thisScript[self.currentSection].get("name")
            else:
                sectionName = "Unnamed Section"
            if sectionName == line:
                text += "<b><font color='blue'>" + line + "</font></b>"
            else:
                text += line
            text += "<br>"
        text += "</ul>"
        return text

    def ReadSections(self):
        sections = self.thisScript.findall("section")
        self.sections = []
        for child in sections:
            if child.tag == "section" and (child.get("os") == None or \
                child.get("os").count(platform.system()) > 0):
                if child.get("name") != None:
                    self.sections.append(child.get("name"))
                else:
                    self.sections.append("Unnamed Section")

    def StartSubProcess(self, args):
        self.subprocessRunning = True
        self.frame.nextBtn.Disable()
        self.frame.openItem.Enable(False)
        self.frame.activityBar.Show(True)
        self.frame.Layout()
        self.subProcessThread = SubProcessThread(args, downloadsFolder,
                                self.frame)
        self.WaitForProcess()

    def WaitForProcess(self):
        import time
        import select
        while self.subprocessRunning:
            wx.Yield()
            if self.subProcessThread.p != None:
                if select.select([self.subProcessThread.p.stdout],
                                 [], [], 0.0)[0]:
                    self.ScriptLog(10 * " " + \
                            self.subProcessThread.p.stdout.readline().rstrip())
                if select.select([self.subProcessThread.p.stderr],
                                 [], [], 0.0)[0]:
                    self.ScriptLog(10 * " " + \
                            self.subProcessThread.p.stderr.readline().rstrip())
            time.sleep(.25)
            wx.Yield()
            self.frame.activityBar.Pulse()

    def EndSubProcess(self, e):
        self.frame.activityBar.Hide()
        self.frame.nextBtn.Enable()
        if self.updatedTools == True:
             self.frame.openItem.Enable(True)
        self.frame.Layout()
        self.subprocessRunning = False

    def DoSubProcess(self, args):
        self.ScriptLog(("DEBUG MODE [" if self.debug else "ACTION  : [") + \
                        ' '.join(args) + "]")
        if not self.debug:
            self.StartSubProcess(args)

    def DoAction(self, action):
        args = []
        for line in action:
            if line.tag == "arg":
                args.append(line.text)
        if action.get("type") == "updatetools":
            self.UpdateTools()
        elif action.get("type") == "adb":
            wfdSkip = action.get("wfd") == "skip"
            self.DoADB(args, wfdSkip)
        elif action.get("type") == "fastboot":
            self.DoFastboot(args)
        elif action.get("type") == "bash":
            self.DoBash(action.text)
        elif action.get("type") == "python":
            external = action.get("external") == "true"
            self.DoPython(action.text, external)
        self.frame.nextBtn.SetFocus()

    def DoBash(self, script):
        script = script.rstrip('\n')
        command = [bash, "-c"]
        self.DoSubProcess(command + [script])

    def DoPython(self, script, external):
        if external:
             command = [python, "-c"]
             self.DoSubProcess(command + [script])
        elif not self.debug:
             self.ScriptLog("Executing Python code: \n" + script)
             exec(script)
        else:
             self.ScriptLog("DEBUG MODE:  Scripted Python code not executed.")

    def DoADB(self, scriptArgs, wfdSkip):
        command = [toolsFolder + androidSdk[3] + "platform-tools/adb"]
        # NOTE:  "wait-for-device" doesn't work with clockworkmod
        # use the wfd="skip" attribute in <action> to override.
        if not wfdSkip:
            self.DoSubProcess(command + ["wait-for-device"])
        self.DoSubProcess(command + scriptArgs)

    def DoFastboot(self, scriptArgs):
        command = [toolsFolder + androidSdk[3] + "platform-tools/fastboot"]
        self.DoSubProcess(command + scriptArgs)

    def UpdateTools(self):

        # copy udev rules file if it doesn't exist already
        # (but the directory for it does)
        if platform.system() == "Linux" and os.path.isdir(udevRules[0]):
            if not os.path.isfile(udevRules[0] + udevRules[1]):
                self.ScriptLog("Copying udev file:  " + udevRules[1] + \
                               " to " + udevRules[0])
                self.DoSubProcess(["cp", os.path.dirname( \
                                os.path.realpath(__file__)) + \
                                "/../" + udevRules[1], udevRules[0] + \
                                udevRules[1]])

        self.ScriptLog("ACTION  : Updating SDK Tools...")
        self.ScriptLog(" " * 10 + "Checking for SDK...")
        attempt = 1
        while not os.access(toolsFolder + androidSdk[3] + "tools/android",
                             os.X_OK):
            self.ScriptLog("Try #" + str(attempt) +
                           ":  Trying to install tools.")
            self.DoSubProcess(["curl", "-sLo" + toolsFolder + androidSdk[1],
                                androidSdk[0] + androidSdk[1]])
            if self.VerifyHash(toolsFolder + androidSdk[1], androidSdk[2], "sha512"):
                self.DoSubProcess(["tar", "-C" + toolsFolder, "-xvf" +
                                   toolsFolder + androidSdk[1]])
            attempt += 1
            if attempt == 6:
                self.ScriptLog("Tried to download the tools 5 times.  Failed.")
                if not self.debug:
                    self.frame.Notify("Just to let you know, this script " +
                             "tried " +
                             "five times to update the tools but was unable " +
                             "to do so.  Please check your Internet " +
                             "connection " +
                             "and try running Derp again.  For now, " +
                             "the script will continue.  This is just for " +
                             "your information.")
                else:
                    self.ScriptLog("(Next time, try running DERP with DEBUG MODE turned off.)")
                break
        else:
            self.ScriptLog("Previous SDK found.  No need to get it again!")

        if os.access(toolsFolder + androidSdk[3] + "tools/android", os.X_OK):
            self.DoSubProcess([toolsFolder + androidSdk[3] + "tools/android",
                            "update", "sdk", \
                            "--no-ui", "--filter", "platform-tool, tool"])
            self.DoSubProcess([toolsFolder + androidSdk[3] + "tools/android",
                               "update", "adb"])
            self.DoSubProcess(["chmod", "-R", "a-w", toolsFolder])
            self.DoSubProcess(["chmod", "-R", "a-w", downloadsFolder])
            self.DoADB(["kill-server"], True)
            self.DoADB(["start-server"], True)
            self.updatedTools = True
            self.frame.openItem.Enable(True)

    def VerifyHash(self, filename, hash, algorithm):
        import hashlib
        try:
            f = open(filename, 'r')
            content = f.read()
            if algorithm.lower() == "md5":
                 h = hashlib.md5(content)
            elif algorithm.lower() == "sha1":
                 h = hashlib.sha1(content)
            elif algorithm.lower() == "sha224":
                 h = hashlib.sha224(content)
            elif algorithm.lower() == "sha256":
                 h = hashlib.sha256(content)
            elif algorithm.lower() == "sha384":
                 h = hashlib.sha384(content)
            elif algorithm.lower() == "sha512":
                 h = hashlib.sha512(content)
        except:
            self.ScriptLog("Error reading file for " + algorithm + \
                 " hash verification. (Does it exist?)")
            return False
        if h.hexdigest() == hash:
            self.ScriptLog(algorithm + " hash checks out for " + filename + ".")
            return True
        else:
            self.ScriptLog(algorithm + " failure for " + filename + "!  File needs to be (re)downloaded.")
            self.ScriptLog("Expected hash : " + hash)
            self.ScriptLog("Actual hash   : " + h.hexdigest())
            return False

    def GetFile(self, filetag):
        success = False
        self.frame.nextBtn.Disable()
        # check hash first, just in case the file is already there.
        if "sha512" in filetag.attrib:
            hash = filetag.get("sha512")
            algorithm = "sha512"
        elif "sha384" in filetag.attrib:
            hash = filetag.get("sha384")
            algorithm = "sha384"
        elif "sha256" in filetag.attrib:
            hash = filetag.get("sha256")
            algorithm = "sha256"
        elif "sha224" in filetag.attrib:
            hash = filetag.get("sha224")
            algorithm = "sha224"
        elif "sha1" in filetag.attrib:
            hash = filetag.get("sha1")
            algorithm = "sha1"
        elif "md5" in filetag.attrib:
            hash = filetag.get("md5")
            algorithm = "md5"
        else:
            self.ScriptLog("ERROR:  <File> tag does not contain a valid hash.")

        if self.VerifyHash(downloadsFolder + filetag.get("local_name"),
                           hash, algorithm):
            success = True
        else:
            attempt = 1
            while attempt < 5:
                self.DoSubProcess(["curl", "-sLo" + downloadsFolder +
                                   filetag.get("local_name"),
                                   filetag.get("url")])
                attempt += 1
                if self.VerifyHash(downloadsFolder + filetag.get("local_name"),
                                  hash, algorithm):
                    success = True
                    break
                elif attempt == 5 and not self.debug:
                    self.frame.Notify("ERROR downloading" +
                        filetag.get("local_name") +
                        " -- Derp tried several times to download " +
                        "this file, but was unable to download and/or " +
                        "verify it.  The script will continue " +
                        "now, but you should know things may go downhill " +
                        "from here.  You may want to " +
                        "check the installation script as well as your " +
                        "Internet connection to see what the deal is.")
        self.frame.nextBtn.Enable()
        self.frame.nextBtn.SetFocus()
        return success

    def SkipOsAttributes(self):

#-- skipping any section/step with the "os" attribute whenever
# that attribute has been
#-- set for a particular OS other than this one.

        sections = self.thisScript.findall("section")
        for num in range(self.currentSection, len(sections)):
            if sections[num].get("os") == None or \
                sections[num].get("os").count(platform.system()) > 0:
                break
            else:
                self.currentSection += 1
                self.currentStep = 0
        if self.currentSection == len(sections):
            self.frame.nextBtn.SetLabel("Finished")
            self.frame.nextBtn.Disable()
            return
        steps = sections[self.currentSection].findall("step")
        for num in range(self.currentStep, len(steps)):
            if steps[num].get("os") == None or \
                steps[num].get("os").count(platform.system()) > 0:
                break
            else:
                self.currentStep += 1
                if self.currentStep >= len(steps):
                    self.currentSection += 1
                    self.currentStep = 0
        if self.currentSection == len(sections):
            self.frame.nextBtn.SetLabel("Finished")
            self.frame.nextBtn.Disable()
            return

    def RunScript(self):

    #--------if it is in the section tag....
        sections = self.thisScript.findall("section")
        if self.currentSection < len(sections):
            section = sections[self.currentSection]
            self.frame.setSection(self.BuildSectionList())
    #--------if it is in the step tag....
            steps = section.findall("step")
            step = steps[self.currentStep]
            if step.get("name") != None:
                self.frame.setInfoTitle(step.get("name"))
            else:
                self.frame.setInfoTitle("Unnamed Step")
    #--------if it is one of the info tags...
            infos = step.findall("info")
            infotext = ""
            for info in infos:
                if info.get("os") == None or \
                    info.get("os").count(platform.system()) > 0:
                    infotext += ET.tostring(info)
            self.frame.setInfo(infotext)
    #--------if it is one of the action tags...
            actions = step.findall("action")
            for action in actions:
                if action.get("os") == None or \
                    action.get("os").count(platform.system()) > 0:
                    self.DoAction(action)
    #--------if it is one of the file tags...
            filetags = step.findall("file")
            for filetag in filetags:
                if filetag.get("os") == None or \
                filetag.get("os").count(platform.system()) > 0:
                    self.GetFile(filetag)
            self.currentStep += 1

            if self.currentStep == len(steps):
                self.currentSection += 1
                self.currentStep = 0

        self.SkipOsAttributes()
    #-------last section?  Disable the continue button
        if self.currentSection == len(sections):
            self.frame.nextBtn.SetLabel("Finished")
            self.frame.nextBtn.Disable()
            self.frame.Update()
            # note.. the above doesn't always seem to work.


class DerpApp(wx.App):

    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        if not os.geteuid() == 0 and platform.system() == "Linux":
            bye = "This program must be run as the Superuser with " + \
                  "full administration access.\n\n" + \
                  "From a Terminal, try:\n\n" + \
                  "sudo python " + \
                   os.path.dirname(os.path.realpath(__file__)) + \
                   "/derp.py" + \
                   "\n\nOr if you installed derp from a package, " + \
                   "you can try:\n\nsudo derp" + \
                   "\n\nYou will be prompted to give your " + \
                   "administrative password."
            wx.MessageBox(bye, "Root Required", wx.OK)
            sys.exit(0)
        Script()

    def MacReopenApp(self):
        self.GetTopWindow().Raise()

    def MacNewFile(self):
        pass

    def MacPrintFile(self, file_path):
        pass


# THE MAIN PROGRAM
def main():
    global app
    app = DerpApp(False)
    app.MainLoop()

if __name__ == "__main__":
    main()
