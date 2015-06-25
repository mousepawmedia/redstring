#!/usr/bin/python

from distutils.core import setup
import py2exe
import sys, os, site, shutil

site_dir = site.getsitepackages()[1]
include_dll_path = os.path.join(site_dir, "gnome")

gtk_dirs_to_include = ['etc', 'lib\\gtk-3.0', 'lib\\girepository-1.0',
'lib\\gio', 'lib\\gdk-pixbuf-2.0', 'share\\glib-2.0', 'share\\fonts',
'share\\icons', 'share\\themes\\Default', 'share\\themes\\HighContrast']

include_gi_path = os.path.join(site_dir, "gi")

gtk_dlls = []
tmp_dlls = []
cdir = os.getcwd()
for dll in os.listdir(include_dll_path):
    if dll.lower().endswith('.dll'):
        gtk_dlls.append(os.path.join(include_dll_path, dll))
        tmp_dlls.append(os.path.join(cdir, dll))

for dll in gtk_dlls:
    shutil.copy(dll, cdir)

#shutil.copy("_gi.pyd", cdir)
            
setup(name="REDSTRING",
    version="2.0.2",
    description="REDundant STRINg Generator",
    author="Jason C. McDonald",
    url="http://www.mousepawgames.com/",
    author_email="info@mousepawgames.com",
    maintainer="MousePaw Labs",
    maintainer_email="info@mousepawgames.com",
    data_files=[("", ["redstring.png", "redstring_interface.glade", "redstring.ico"])],
    #py_modules=["redstring"],
    windows=[
        {
            'script': 'redstring.py',
            "icon-resources": [(1, "redstring.ico")]
            }
        ],
    options={"py2exe": {
        "unbuffered": True,
        "compressed": True,
        "bundle_files": 3,
        'packages': ['gi'],
        'includes': ['gi'],
        }},
    zipfile=None,
    )

dest_dir = os.path.join(cdir, 'dist')
for dll in tmp_dlls:
    shutil.copy(dll, dest_dir)
    os.remove(dll)

for d in gtk_dirs_to_include:
    shutil.copytree(os.path.join(site_dir, "gnome", d),
        os.path.join(dest_dir, d))
