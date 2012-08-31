#!/usr/bin/env python

"""Switch between several configurations for a particular device pair."""

import mapper
import wx

devices = ['/tkgui.1', '/tk_pwm.1']

configs = [
    {'name': 'Duty', 'connections': [('/signal0', '/duty',
                                      {'mode': mapper.MO_BYPASS,})]},
    {'name': 'Freq', 'connections': [('/signal0', '/freq')]},
    {'name': 'Gain', 'connections': [('/signal0', '/gain')]},
]

class SwitcherFrame(wx.Frame):
    def __init__(self, parent, title, devices, configurations):
        wx.Frame.__init__(self, parent, title=title, size=(300,500))

        self.monitor = mapper.monitor()

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(100) # every 100 ms

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        self.devices = devices
        self.configs = configurations
        self.selected = None

        self.buttons = {}
        for c in self.configs:
            button = wx.Button(panel, id=-1, label=c['name'],
                               pos=(8, 8), size=(280, 28))
            button.Bind(wx.EVT_BUTTON, self.on_click(c))
            box.Add(button, 0, wx.ALL, 10)
            self.buttons[c['name']] = button

        panel.SetSizer(box)
        panel.Layout()

    def OnExit(self, event):
        if self.OnSave(None):
            self.Destroy()

    def OnTimer(self, event):
        self.monitor.poll(0)

    def on_click(self, config):
        def handler(event):
            self.SetTitle("%s clicked"%config['name'])
            for b in self.buttons:
                self.buttons[b].SetForegroundColour("Black");
            self.buttons[config['name']].SetForegroundColour("Blue");
            self.selected = config
            self.monitor.request_links_by_name(devices[0])
            self.monitor.request_connections_by_name(devices[0])

            db = self.monitor.db
            if db.link_by_src_dest_names(*devices)==None:
                self.monitor.link(*devices)

            cons = dict([((devices[0]+c[0], devices[1]+c[1]), c)
                         for c in config['connections']])
            for con in db.connections_by_src_dest_device_names(*devices):
                c = con['src_name'], con['dest_name']
                if c in cons:
                    if (len(cons[c])>2
                        and any([cons[c][2][p]!=con[p]
                                 for p in cons[c][2]])):
                        d = {'src_name': c[0], 'dest_name':c[1]}
                        for p in cons[c][2]:
                            d[p] = cons[c][2][p]
                        self.monitor.modify(d)
                    del cons[c]
                else:
                    self.monitor.disconnect(*c)
            for c in cons:
                self.monitor.connect(c[0],c[1], *cons[c][2:])

        return handler
    
if __name__=="__main__":
    if not globals().has_key('app'):
        app = wx.App(False)
    frame = SwitcherFrame(None, "Mapper Switcher", devices, configs)
    frame.Show(True)
    frame.SetFocus()
    app.MainLoop()
