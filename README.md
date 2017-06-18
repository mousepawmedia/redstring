# Redstring 2.0.2

**Redstring** is distributed by MousePaw Media
(formerly MousePaw Games/MousePaw Labs).
See the [official project page][1].

## Description

Life is full of redundancy. Whether you need to
write fifty lines of code that follows the same
format, generate a thousand serial numbers from a
pattern, or write eight hundred sentences for
teaching the letter “D”, REDSTRING can help.

## Installation

### Windows

#### Prerequisites

None known. The executable runs without Python being installed on
the computer.

#### Install

Run `Redstring-2.0.2-Setup.exe` to start the installer. All needed
files will be installed.

#### Run, Win XP/Vista/7

Go to START -> MousePaw Labs -> Redstring.

#### Run, Win 8/8.1

Go to Start Screen, type "Redstring" to search for app.

### Linux

#### Prerequisites

Install Python 2.7 or later, as well as the GTK+3 bindings.

	sudo apt-get install python
	sudo apt-get install python-gi

-OR-

	sudo apt-get install python3
	sudo apt-get install python3-gi

#### Install

Download `Redstring-2.0.2.zip`. Unpack in your home directory. The file
"Redstring" is an executable Python file.

#### Run

In a terminal, browse to your Redstring folder.

	cd Redstring

Execute the Redstring file.

	./Redstring

## Development Notes

Redstring was written in Python 2.7 and GTK 3.8 (PyGObject), using...

Primary Development Operating System [Ubuntu 14.14](http://www.ubuntu.com/)

Integrated Development Environment [NINJA-IDE](http://ninja-ide.org/)

GUI RAD [Glade](https://glade.gnome.org/)

Testing Environment [VirtualBox](https://www.virtualbox.org/)

Windows Binary Creator [Py2Exe](http://www.py2exe.org/)

Windows Installer Creator [InnoSetup]([http://www.jrsoftware.org/isinfo.php)
[Inno Script Studio](https://www.kymoto.org/)

Other Packaging Tools [ResourceHacker](http://www.angusj.com/resourcehackr/)
[ConvertICO.org](http://convertico.org/)

Some code authored using Redstring 2.0.2... yes, this project is recusive.

The full source code is available at [GitHub][5]


## Jason C. McDonald would like to thank...

The team at MousePaw Media, especially Jane McArthur and Anne McDonald.

The good people of StackOverflow for helping me out of a few big problems.

The great guys on the `#python` IRC channel on Freenode, where I practically
lived for three days.

(Special thanks to dash on #python for solving the project's biggest and most
annoying bug.)

## Contributions

We do not accept pull requests through GitHub.
If you would like to contribute code, please read our [Contribution Guide][2].

All contributions are licensed to us under the
[MousePaw Media Terms of Development][3].

## License

Anari is licensed under the GNU General Public License 3.0. (See LICENSE.md)

The project is owned and maintained by [MousePaw Media][2].

[1]: https://www.mousepawmedia.com/redstring
[2]: https://www.mousepawmedia.com/
[3]: https://www.mousepawmedia.com/developers/contributing
[4]: https://www.mousepawmedia.com/termsofdevelopment
[5]: https://github.com/mousepawmedia/restring
