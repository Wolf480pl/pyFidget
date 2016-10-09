#!/usr/bin/python2

##
# This file is part of pyFidget, licensed under the MIT License (MIT).
#
# Copyright (c) 2016 Wolf480pl <wolf480@interia.pl>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo, pango, pangocairo
from time import time, sleep
import threading
import math

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

def transformPoint(point, mtx):
    ex1, ey1, ex2, ey2, x0, y0 = mtx
    i1, i2 = point
    return (
        i1 * ex1 + i2 * ex2 + x0,
        i1 * ey1 + i2 * ey2 + y0
    )

def toShapeMap(surface):
    width = surface.get_width()
    height = surface.get_height()

    bitmap = gtk.gdk.Pixmap(None, width, height, 1)
    bmpCr = bitmap.cairo_create()

    patt = cairo.SurfacePattern(surface)
    bmpCr.set_source(patt)
    bmpCr.set_operator(cairo.OPERATOR_SOURCE)
    bmpCr.paint()

    return bmpCr, bitmap

class Screen(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }

    _time = time()
    _shapemap = None
    _bubbletext = None
    _bubbletime = 0

    def __init__(self, animation, texture, getFrameRect, config):
        gtk.DrawingArea.__init__(self)
        self._fidget = animation
        self._texture = cairo.ImageSurface.create_from_png(texture)
        self._getFrameRect = getFrameRect
        self._patt = cairo.SurfacePattern(self._texture)
        self._config = config

    def showBubble(self, text, time=5):
        self._bubbletext = text
        self._bubbletime = time
        print(text, time)

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

        self.draw(cr, *self.window.get_size())

    def draw(self, cr, width, height):
        t = time()
        dt = t - self._time
        self._time = t
        dtmill = int(dt * 1000)
        if (dtmill > 20000):
            # We're realy late, waaay behind the schedule
            # There's no way we're gonna catch up
            # But guess what? It doesn't matter!
            # We can just set dt to something low, and the next frame will be correct
            print("warning: skipping a very long tick: %d" % dtmill)
            dtmill = 1
        self._fidget.update(dtmill)

        self.clear(cr)

        cr.save()
        offset = self._config.get("offset", (0, 0))
        cr.translate(*offset)

        if hasattr(self._fidget, 'transforms'):
            for mtx in self._fidget.transforms():
                cr.transform(cairo.Matrix(*mtx))

        for state in self._fidget.state():
            cr.save()
            mtx = self._patt.get_matrix()
            self.drawState(cr, state)
            self._patt.set_matrix(mtx)
            cr.restore()

        cr.restore()
        if self._bubbletext:
            self.drawBubble(cr, self._bubbletext)
            self._bubbletime -= dt;
            if (self._bubbletime <= 0):
                self._bubbletime = 0
                self._bubbletext = None

        tgtSurface = cr.get_target()

        bmpCr, shapemap = toShapeMap(tgtSurface)

        self._shapemap = shapemap

        #dbgPatt = cairo.SurfacePattern(bmpCr.get_target())
        #cr.set_source(dbgPatt)
        #cr.set_operator(cairo.OPERATOR_SOURCE)
        #cr.paint()

    def drawBubble(self, cr, text):
        cr.save()

        pgctx = pangocairo.CairoContext(cr)
        pgctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        layout = pgctx.create_layout()
        font = pango.FontDescription("Sans 10")
        layout.set_font_description(font)

        layout.set_text(text)
        extents, _ = layout.get_pixel_extents()
        x_bear, y_bear, w, h = extents
        radius = self._config.get("radius", 10)
        bubpos_x, bubpos_y = self._config.get("bubble-pos", (150.5, 0.5))
        bubborder_color = self._config.get("bubble-border-color", (1, .5, 0, 1))
        bubbg_color = self._config.get("bubble-bg-color", (0, 0, 0, 0.5))
        text_color = self._config.get("bubble-text-color", (1, 1, 1, 1))
        bubtail_pad = self._config.get("bubble-tail-pad", 5)
        bubtail_width = self._config.get("bubble-tail-width", 10)
        bezi_x, bezi_y = self._config.get("bubble-bezier", (0, 30))

        mouth_x, mouth_y = 0, 0
        mouth = self._fidget.attachment("mouth")
        if mouth:
            mouth = reduce(transformPoint, self._fidget.transforms(), mouth)
            mouth_x, mouth_y = mouth

        cr.translate(bubpos_x + radius, bubpos_y + radius)
        mouth_x -= bubpos_x + radius
        mouth_y -= bubpos_y + radius

        cr.set_source_rgba(*bubborder_color)
        cr.set_line_width(1)
        cr.move_to(0, -radius)
        cr.rel_line_to(w, 0)
        cr.arc(w, 0, radius, -math.pi / 2, 0)
        cr.rel_line_to(0, h)
        cr.arc(w, h, radius, 0, math.pi / 2)

        if not mouth:
            cr.rel_line_to(-w, 0)
        else:
            cr.rel_line_to(-w + bubtail_pad + bubtail_width, 0)
            curx, cury = cr.get_current_point()
            cr.curve_to(curx + bezi_x, cury + bezi_y, mouth_x, mouth_y, mouth_x, mouth_y)
            curx -= bubtail_width
            cr.curve_to(mouth_x, mouth_y, curx + bezi_x, cury + bezi_y, curx, cury)
            cr.rel_line_to(-bubtail_pad, 0)

        cr.arc(0, h, radius, math.pi / 2, math.pi)
        cr.rel_line_to(0, -h)
        cr.arc(0, 0, radius, -math.pi, - math.pi / 2)
        cr.stroke_preserve()
        cr.set_source_rgba(*bubbg_color)
        cr.fill()

        cr.set_source_rgba(*text_color)
        cr.translate(-x_bear, -y_bear)

        pgctx.update_layout(layout)
        pgctx.show_layout(layout)

        #cr.move_to(0, 0)
        #cr.show_text(text)

        cr.restore()

    def shapemap(self):
        return self._shapemap

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
        (sx, sy, w, h) = self._getFrameRect(f)
        surf = self._patt

        mdst = mkMatrix((x, y), p1, p2, (w, h))
        cr.transform(mdst)

        m = cairo.Matrix()
        m.translate(sx, sy)
        surf.set_matrix(m)
        cr.set_source(surf)
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
            gtk.threads_enter()
            self.window.queue_draw()
            self.window.queue_resize()
            gtk.threads_leave()

class BubbleReader(threading.Thread):
    def __init__(self, widget):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.widget = widget
        self.path = "./fidget.sock"

    def run(self):
        import sys, os, socket
        try:
            os.unlink(self.path)
        except:
            if (os.path.exists(self.path)):
                raise

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.path)
        sock.listen(1)

        while True:
            conn, addr = sock.accept()
            for line in conn.makefile():
                self.widget.showBubble(line[:-1])


# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(animation, texture, getFrameRect, config):
    #size=(200, 200), offset=(0, 0)
    size = config.get("size", (200, 200))
    
    gtk.threads_init()
    gtk.threads_enter()

    window = gtk.Window()

    widget = Screen(animation, texture, getFrameRect, config)
    widget.show()

    def on_size_allocate(wind, rect):
        #print("walloc")
        shapemap = widget.shapemap()
        if shapemap:
            window.input_shape_combine_mask(shapemap, 0, 0)
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
    window.set_default_size(*size)

    colormap = window.get_screen().get_rgba_colormap()
    gtk.widget_set_default_colormap(colormap)

    window.present()
    refresher = Refresher(window)
    refresher.start()
    reader = BubbleReader(widget)
    reader.start()
    try:
        gtk.main()
    finally:
        gtk.threads_leave()

def rgb24to32(data):
    itr = iter(data)
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
    if (pb != None):
        myw, myh = 512, 300
        pb = pb.subpixbuf(x, y, myw, myh)
        w, h = myw * 2, myh / 2
        format = cairo.FORMAT_ARGB32
        stride = cairo.ImageSurface.format_stride_for_width(format, w)
        im = cairo.ImageSurface.create_for_data(rgb24to32(pb.get_pixels()), format, w, h, stride)
        return im

import fidget

if __name__ == "__main__":
    print("This way of starting Fidget is deprecated. Please run cairoFidget.py instead.")
    run(fidget.Fidget(), "fidget-sprites.png", fidget.getFrameRect, {"size": (121, 121), "offset": (-53, -17)})
