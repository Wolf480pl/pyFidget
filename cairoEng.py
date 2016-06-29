#!/usr/bin/python2

import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
from time import time, sleep
import threading

from fidget import Fidget, getFrameRect


def mkFidget():
    fidget = Fidget()
    return fidget

def mkMatrix(p0, p1, p2, size):
    w, h = size
    w, h = float(w), float(h)
    x0, y0 = p0
    if p1:
        x1, y1 = p1
        dx1, dy1 = x1 - x0, y1 - y0
        ex1, ey1 = dx1 / w, dy1 / w
    else:
        ex1, ey1 = 1, 0
    if p2:    
        x2, y2 = p2
        dx2, dy2 = x2 - x0, y2 - y0
        ex2, ey2 = dx2 / h, dy2 / h
    else:
        ex2, ey2 = 0, 1
    
    return cairo.Matrix(ex1, ey1,
                        ex2, ey2,
                        x0 , y0 )

class Screen(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }
    
    _fidget = mkFidget()
    _time = time()
    _texture = cairo.ImageSurface.create_from_png("fidget-sprites.png")
    _patt = cairo.SurfacePattern(_texture)
    _bitmap = None
    
    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        if not hasattr(self, 'bg') :
            if self.is_composited():
                print("Composite! \o/")
                self.bg = None
            else:
                self.bg = capt_screen(self)
        
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
        
        #print(cr.get_matrix())
        cr.transform(cairo.Matrix(1, 0,
                                  -0.4, 1,
                                  0, 0))
        
        #cr.set_source(cairo.SurfacePattern(surf));
        cr.set_source(gradient)
        #cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(40, 10, width - 80, height - 20)
        cr.fill()

    def draw2(self, cr, width, height):
        #print("draw")
        t = time()
        dt = t - self._time
        self._time = t
        dtmill = int(dt * 1000)
        #print(dtmill)
        self._fidget.update(dtmill)
        
        self.clear(cr)

        cr.save()
        cr.translate(-53, -17)
        
        for state in self._fidget.state():
            cr.save()
            mtx = self._patt.get_matrix()
            self.drawState(cr, state)
            self._patt.set_matrix(mtx)
            cr.restore()

        cr.restore()
        tgtSurface = cr.get_target()
        
        alphaMap = tgtSurface.create_similar(cairo.CONTENT_COLOR_ALPHA, width, height)
        alphaCr = cairo.Context(alphaMap)
        
        alphaPatt = cairo.SurfacePattern(tgtSurface)
        alphaCr.set_source(alphaPatt)
        alphaCr.set_operator(cairo.OPERATOR_SOURCE)
        alphaCr.paint()
        
        alphaCr.set_source_rgb(1, 1, 1)
        alphaCr.set_operator(cairo.OPERATOR_IN)
        alphaCr.paint()
        
        bitmap = gtk.gdk.Pixmap(None, width, height, 1)
        bmpCr = bitmap.cairo_create()
        #bmpCr = cr
        bmpCr.set_source_rgb(0, 0, 0)
        bmpCr.set_operator(cairo.OPERATOR_CLEAR)
        bmpCr.paint()

        bmpPatt = cairo.SurfacePattern(alphaMap)
        bmpCr.set_source(bmpPatt)
        #bmpCr.set_source_rgb(1.0, 1.0, 1.0)
        bmpCr.set_operator(cairo.OPERATOR_SOURCE)
        #bmpCr.rectangle(10, 10, 90, 40)
        bmpCr.paint()
        #bmpCr.fill()

        self._bitmap = bitmap

        dbgPatt = cairo.SurfacePattern(bmpCr.get_target())
        cr.set_source(dbgPatt)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        #cr.paint()

        #self.shape_combine_mask(bitmap, 0, 0)
    
#    def do_size_allocate(self, *args):
#        gtk.DrawingArea.do_size_allocate(self, *args)
#        print("alloc")
#        if self._bitmap:
#            self.window.shape_combine_mask(self._bitmap, 0, 0)
#            print("alloc with bitmap")

    def clear(self, cr):
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        if self.bg:
            bg = cairo.SurfacePattern(self.bg)
            cr.set_source(bg)
        else:
            cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.restore()

    def drawState(self, cr, state):
        ((x, y), f, p1, p2) = state
        (sx, sy, w, h) = getFrameRect(f)
        surf = self._patt

#        mdst = cairo.Matrix(
#               1, 0,
#            tilt, 1,
#               x, y
#        )
        mdst = mkMatrix((x, y), p1, p2, (w, h))
        #cr.translate(x, y)
        cr.transform(mdst)

        m = cairo.Matrix()
        m.translate(sx, sy)
        surf.set_matrix(m)
        #print(f, sx, sy, w, h)
        cr.set_source(surf)
        #print(x, y)
        cr.rectangle(0, 0, w, h)
        cr.fill()

class Refresher(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.window = window
    
    def run(self):
        fps = 60
        tick = 1.0 / fps
        while True:
            sleep(tick)
            #print("tick")
            gtk.threads_enter()
            self.window.queue_draw()
            self.window.queue_resize()
            gtk.threads_leave()

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(Widget):
    gtk.threads_init()
    gtk.threads_enter()
    
    window = gtk.Window()

    widget = Widget()
    widget.show()

    def on_size_allocate(wind, rect):
        #print("walloc")
        if widget._bitmap:
            window.input_shape_combine_mask(widget._bitmap, 0, 0)
            #window.reset_shapes()
            #print("walloc with bitmap")        

    window.connect("delete-event", gtk.main_quit)
    window.connect("size-allocate", on_size_allocate)
    window.add(widget)
    window.set_decorated(False)
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_keep_above(True)
    window.stick()
    window.set_default_size(121, 121)

    colormap = window.get_screen().get_rgba_colormap()
    gtk.widget_set_default_colormap(colormap)
        
    window.present()
    refresher = Refresher(window)
    refresher.start()
    try:
        gtk.main()
    finally:
        gtk.threads_leave()

def rgb24to32(data):
    itr = iter(data)
    #out = bytearray(len(data) / 3 * 4)
    out = bytearray()
    try:
        while True:
            r = next(itr)
            g = next(itr)
            b = next(itr)
            out.append(b)
            out.append(g)
            out.append(r)
            out.append(0)
    except StopIteration:
        pass
    return out

def capt_screen(widget):
    x, y = widget.window.get_position()
    win = gtk.gdk.get_default_root_window()
    w, h = win.get_size()
    pb = gtk.gdk.Pixbuf(0 , False, 8, w, h)
    widget.hide()
    pb = pb.get_from_drawable(win, win.get_colormap(), 0, 0, 0, 0, w, h)
    widget.show_all()
    #return pb
    if (pb != None):
#        myw, myh = widget.window.get_size()
        myw, myh = 512, 300
        pb = pb.subpixbuf(x, y, myw, myh)
        w, h = myw * 2, myh / 2
        format = cairo.FORMAT_ARGB32
        stride = cairo.ImageSurface.format_stride_for_width(format, w)
        im = cairo.ImageSurface.create_for_data(rgb24to32(pb.get_pixels()), format, w, h, stride)
        return im
    #    im = Image.fromstring('RGB', (w, h), pb.get_pixels())
    #    im = im.crop((x, y, x + self._w, y + self._h))
    #    im = im.convert('RGBA') 
    #    return im #or pb

if __name__ == "__main__":
    run(Screen)
