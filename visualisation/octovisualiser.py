#!/usr/bin/env python

import Tkinter, sys, math, mapper

N = int(sys.argv[1])
values = [0.5]*N

def on_sig(n,v):
    values[n] = v
    redraw()

dev = mapper.device("octovisualiser", 9000)
sigs = [dev.add_input("/arm.%d"%n, 1, 'f',
                      None, 0.0, 1.0, (lambda n: lambda s,f: on_sig(n,f))(n))
        for n in range(N)]

root = Tkinter.Tk()

canvas = Tkinter.Canvas(root, width=400, height=400)
canvas.pack()

def redraw():
    canvas.delete("all")
    radius = 150
    for n in range(N):
        canvas.create_line(200, 200,
                           200 + math.cos(float(n)/N*2*math.pi)*radius,
                           200 + math.sin(float(n)/N*2*math.pi)*radius,
                           smooth=1)
    poly = []
    for n,v in enumerate(values):
        poly += [200 + math.cos(float(n)/N*2*math.pi)*radius*v,
                 200 + math.sin(float(n)/N*2*math.pi)*radius*v]
    canvas.create_polygon(*poly, outline='black')
redraw()

def update():
    dev.poll(10)
    root.after(100, update)

root.after(100, update)
root.mainloop()
