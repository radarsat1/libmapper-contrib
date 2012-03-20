#!/usr/bin/env python

"""Program to pop up a text box for editing a mapping function.
Inputs and outputs of the function are exposed as libmapper
signals."""

import wx
import mapper
import sys, os, threading, Queue

done = False
def process(*x):
    print 'default process'
processfunc = [process]
#process = lambda: None
que = Queue.Queue()

def deviceLoop():
    inputidx = {}
    outputsigs = {}
    args = []
    got_new_values = [False]

    def h(sig, f):
        if inputidx.has_key(sig.name):
            args[inputidx[sig.name]] = f
            got_new_values[0] = True

    dev = mapper.device("functionMapper", 9000)
    inplist = set([])
    outlist = set([])
    while not done:
        dev.poll(10)
        if got_new_values[0]:
            got_new_values[0] = False
            try:
                result = processfunc[0](*args)
                if result.__class__ == int or result.__class__ == float:
                    outs = {'output00': result}
                elif result.__class__ == list:
                    outs = dict([('output%02d'%i,x)
                                 for i,x in enumrate(result)])
                elif result.__class__ == dict:
                    outs = result
                else:
                    outs = {}
                for o in outs:
                    outputsigs[o].update(result[o])
            except Exception, e:
                print e
        while not que.empty():
            newinplist, newoutlist = que.get()

            diff = set(newinplist).difference(inplist)
            inplist.update(newinplist)
            for n,i in enumerate(newinplist):
                inputidx['/'+i] = n
            for i in diff:
                dev.add_input('/'+i, 1, 'f', None, None, None, h)
            while len(args) < len(inplist):
                args.append(0)

            diff = set(newoutlist).difference(outlist)
            outlist.update(newoutlist)
            for o in diff:
                outputsigs[o] = dev.add_output('/'+o, 1, 'f', None, None, None)

    del dev

class FunctionEntryFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(400,500))

        self.CreateStatusBar()

        filemenu = wx.Menu()
        filemenu.AppendSeparator()

        menuSave = filemenu.Append(wx.ID_SAVE,"&Save","Save current state")
        self.Bind(wx.EVT_MENU, self.OnSave, menuSave)

        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit","Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File")
        self.SetMenuBar(menuBar)

        self.textwidget = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        font1 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL,
                        False, u'courier') 
        self.textwidget.SetFont(font1) 

        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.OnRestore(None)

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000) # every second

    def OnExit(self, event):
        if self.OnSave(None):
            self.Destroy()

    def filename(self):
        if len(sys.argv) > 1:
            return sys.argv[1]
        else:
            return os.path.join(os.environ['HOME'], '.functionMapper')

    def OnSave(self, event):
        try:
            f = open(self.filename(), 'w')
            f.write(self.textwidget.GetValue())
            return True
        except Exception, e:
            print 'Failed to write to', self.filename()
            print e
            return False

    def OnRestore(self, event):
        try:
            f = open(self.filename(), 'r')
            self.textwidget.SetValue(f.read())
        except Exception, e:
            self.textwidget.SetValue("""
# Optionally, add more named parameters.
# Return a list of values or a dict.

def process(x):
    return {'y': x*10}
""")
        self.LoadNewCode(self.textwidget.GetValue())

    def OnTimer(self, event):
        if self.textwidget.IsModified():
            self.LoadNewCode(self.textwidget.GetValue())
            self.textwidget.DiscardEdits()

    def LoadNewCode(self, code):
        global processfunc
        try:
            compiled = compile(code, 'functionMapper', 'exec')
            exec compiled
            result = process(*range(len(process.func_code.co_varnames)))
            if result.__class__ == int or result.__class__ == float:
                outs = ['output00']
            elif result.__class__ == list:
                outs = ['output%02d'%x for x in range(len(result))]
            elif result.__class__ == dict:
                outs = result.keys()
            else:
                outs = []
            que.put((process.func_code.co_varnames,outs))
            processfunc[0] = process
        except Exception, e:
            print e

if __name__=="__main__":
    if not globals().has_key('app'):
        app = wx.App(False)
    frame = FunctionEntryFrame(None, "functionMapper")
    frame.Show(True)
    frame.SetFocus()
    thread = threading.Thread(target=deviceLoop)
    thread.start()
    app.MainLoop()
    done = True
    thread.join()
