# pyFidget

A widget of Fidget from [Dust:AET] flying on top of your desktop.

Written in Python 2, with pygtk and pycairo.

Designed so that it's easy to adapt for other animations and add support for other graphic libraries.

## Screenshot

![fidget screenshot](https://raw.githubusercontent.com/Wolf480pl/pyFidget/master/screenshot.png)

## Usage

You need Python 2 and pygtk.

Simply run the `cairoFidget.py` file.

This has ben only tested on Linux.

Apparently, there do exist versions of GTK, Python, and PyGTK for other 
platforms (*BSD, OS X, Windows), but I haven't tested it.
If you test it on one of those platforms, please, let me know how it went :)

Transparency currently works very well on X11 with a compositing winow manager
(or with a standalone compositor, like `xcompmgr` or `compton`).
There is a (hackish) workaround for non-compositing WMs, but I forgot whether it
works well.

Input shape (click-through-ness of the transparent area near Fidget) works well
on X11.

## Copying

The code is under the MIT License, see `LICENSE.txt`

The coordinates, timings, etc. of the animations in the code are from slow's
[DesktopFidget], also under MIT.

The fidget-sprites.png file was copied from [DesktopFidget] and, as far as I know,
is copyrighted by [Dean Dodrill], the autor of [Dust:AET], and not under MIT.
He said it's ok for me to use it.

[Dust:AET]: http://www.noogy.com/main.html
[DesktopFidget]: https://github.com/slow3586/DesktopFidget
[Dean Dodrill]: http://www.noogy.com/
