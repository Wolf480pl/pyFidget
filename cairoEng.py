#!/usr/bin/python2

import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
from time import time, sleep
import threading

from fidget import Fidget, getFrameRect


class Screen(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }
    
    _fidget = Fidget()
    _time = 0
    _texture = cairo.ImageSurface.create_from_png("fidget-sprites.png")
    _patt = cairo.SurfacePattern(_texture)
    
    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw2(cr, *self.window.get_size())

    def draw(self, cr, width, height):
        # Fill the background with gray
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        gradient = cairo.LinearGradient(0, 0, 128, 0);
        gradient.add_color_stop_rgb(0, 255, 0, 0);
        gradient.add_color_stop_rgb(256, 255, 255, 0);
        #print(gradient)
        
        print(cr.get_matrix())
        cr.transform(cairo.Matrix(1, 0,
                                  -0.4, 1,
                                  0, 0))
        
        #cr.set_source(cairo.SurfacePattern(surf));
        cr.set_source(gradient)
        #cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(40, 10, width - 80, height - 20)
        cr.fill()

    def draw2(self, cr, width, height):
        print("draw")
        t = time()
        dt = t - self._time
        self._time = t
        self._fidget.update(dt)
        
        for state in self._fidget.state():
            cr.save()
            mtx = self._patt.get_matrix()
            self.drawState(cr, state)
            self._patt.set_matrix(mtx)
            cr.restore()

    def drawState(self, cr, state):
        ((x, y), f) = state
        (sx, sy, w, h) = getFrameRect(f)
        surf = self._patt
        m = cairo.Matrix()
        m.translate(sx, sy)
        surf.set_matrix(m)
        cr.set_source(surf)
        #cr.translate(x, y)
        #cr.transform(cairo.Matrix())
        cr.rectangle(0, 0, w, h)
        cr.fill()

class Refresher(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window
    
    def run(self):
        fps = 30
        tick = 1.0 / fps
        while True:
            sleep(tick)
            print("tick")
            self.window.queue_draw()

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(Widget):
    gtk.threads_init()
    gtk.threads_enter()
    
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    widget = Widget()
    widget.show()
    window.add(widget)
    window.present()
    Refresher(window).start()
    gtk.main()
    
    gtk.threads_leave()

if __name__ == "__main__":
    run(Screen)
