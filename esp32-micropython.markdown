---
layout: page
title: ESP32 MicroPython Installation Guide for 492
---
# Intro
This is a guide for how to get up and running with MicroPython on a common ESP32 development board. The guide will be similar to the official Micropython guide for [Getting started with MicroPython on the ESP32](http://docs.micropython.org/en/latest/esp32/tutorial/intro.html#esp32-intro).

# What's MicroPython?

MicroPython is a software implementation for Python 3 adapted for microcontrollers. You have most of the features of Python 3, plus some device-specific APIs for I.O. like for GPIO and SPI and stuff.

Read more about it here: https://micropython.org/

Or check out the official documentation here: http://docs.micropython.org/en/latest/

# Prerequisites:
To start, you'll need to have Python 3 installed. If you don't have Python 3, get it here: https://www.python.org/downloads/ . Make sure Python is in your PATH.

I'm assuming you're running Windows. If you're running Linux, you probably know how to translate commands to a Linux equivalent. I.e. call `python3` and `pip3` instead of `python` or `pip` since `python` might default to Python 2 (check with `python --version`). Use `screen` or a serial console to `/dev/ttyS0` instead of PuTTY to `COM1`, etc.

# Installing the MicroPython firmware

### Installing esptool

You'll need Espressif's [esptool](https://github.com/espressif/esptool/) to flash the bootloader on your ESP32.

Once you know Python is installed, open CMD or your choice of terminal and type `pip install esptool`.

![](https://i.imgur.com/3TK5XT2.png)

To check whether esptool was installed, run `esptool.py` in your terminal. You should get the esptool version and help.

![](https://i.imgur.com/3BOD3e3.png)

### Downloading and installing MicroPython

You'll need to download the binary for the firmware for the ESP32. Here's the download page: https://micropython.org/download/esp32/

I am using the latest stable GENERIC build with support for BLE, LAN, and PPP. At the time of writing, that is [esp32-idf3-20200902-v1.13.bin](https://micropython.org/resources/firmware/esp32-idf3-20200902-v1.13.bin).

Note: **THE FOLLOWING STEPS WILL ERASE ANYTHING STORED ON THE ESP32**. You can restore the original ESP-IDF firmware later using their development environment.

In your terminal, navigate to the folder where you put the .bin file. If you have the folder open in Windows File Explorer, you can click on the address bar, type `cmd`, and hit enter. This will open a command prompt at the current path of the Explorer window.

You will need to find the serial address of your ESP32 board on your computer. Connect your ESP32 to your computer using a micro-USB cable. Then, open *Device Manager*. You can do this quickly by right-clicking on the Start button and choosing *Device Manager*. Then, find the section titled *Ports (COM & LPT)* and expand it. Your ESP32 will be listed in this section. Figure out which one it is. The entry will have the serial COM port number listed next to it. For example, in the picture below, my ESP32 is on `COM5`.

![](https://i.imgur.com/UzO5ASn.png)

To erase the flash, in your terminal, enter `esptool.py --port COM5 erase_flash` where `COM5` is replaced with the serial address of your ESP32.

![](https://i.imgur.com/1pKzXIF.png)

Then, to write the firmware, enter `esptool.py --chip esp32 --port COM5 write_flash -z 0x1000 esp32-idf3-20200902-v1.13.bin`

You will need to replace the `COM5` with the serial port you found earlier. Replace the last argument, `esp32-idf3-20200902-v1.13.bin`, with the file name of the firmware that you downloaded earlier. Remember that you should be running this in the same directory as the firmware file.

The esptool.py will flash the ESP32 with the MicroPython firmware and verify that it was written correctly.

![](https://i.imgur.com/oyIUTaX.png)

Congratulations! MicroPython should now be installed on your ESP32!

# Getting a REPL Prompt

MicroPython is an interpreted language with its own REPL prompt. We can get an interactive prompt that runs off our ESP32 and run commands right on the microcontroller! We're going to do this through a serial connection first.

Open PuTTY. For *Connection type:*, choose `Serial`. For *Serial line*, type in the COM port you found earlier. In my case, it's `COM5`. For *Speed*, use a baud rate of `115200`.

![](https://i.imgur.com/w7zur7Y.png)

Click *Open*. PuTTY should connect to your ESP32 and you should see something like this:

![](https://i.imgur.com/kclgE7m.png)

If so, try typing `print("Hello, world!")` and hit enter. You should get a response back.

![](https://i.imgur.com/XLHhJUV.png)

Congrats! You've just run MicroPython on your ESP32! If you really wanted to, you could write a whole program like this.

# File transfer

Okay, but how do we run .py files on the ESP32? Well, first, we need a way to transfer files to the board. [This article](https://www.digikey.com/en/maker/projects/micropython-basics-load-files-run-code/fb1fcedaf11e4547943abfdd8ad825ce) mentions several methods of doing so, like the web REPL, which can be accessed over Wi-Fi, rshell, and mpfshell. But it explains how to use Adafruit's **ampy** tool over a serial USB connection to do so. We've already got our ESP32 plugged in, so let's try that.

Go back to your terminal, and run `pip install adafruit-ampy`. The tool should then install.

To verify that the tool works, run `ampy` in your terminal. You should get the help file.

Let's try transfering a file. First, we need a file to run. Make a file called `hello.py` and put the following line in it: `print("Hello again!")`

Then, open a terminal at the location of the `hello.py` file and run `ampy --port COM5 put hello.py`. This will transfer the `hello.py` file to the root directory of your ESP32's file system, overwriting any existing hello.py file.

**Note: Only one program can open the serial connection to your ESP32 at a time. If you still have a PuTTY connected to your ESP32, close it!**

Now, try running the file. In your terminal, run `ampy --port COM5 run hello.py`. You should see a response.

Congrats! You've just transferred a file to your ESP32! For more info on the `ampy` tool, check out the article linked above. Or just run `ampy` in your terminal for a quick refresher.

# Other topics

Other workflow things you can try include setting up your ESP32 to connect to your Wi-Fi, which will allow you to access the webREPL prompt and upload files to the ESP32 without a serial connection.

# Wi-Fi and WebREPL setup overview

Follow the instructions in the [Networking section of the MicroPython ESP32 quick reference](http://docs.micropython.org/en/latest/esp32/quickref.html#networking) to get your ESP32 connected to the Wi-Fi. Download the `boot.py` file from your ESP32 using `ampy` or something. Add the code from the Networking section to the `boot.py` so that it runs when the ESP32 starts up.

Follow the instructions in the [WebREPL section](http://docs.micropython.org/en/latest/esp32/quickref.html#webrepl-web-browser-interactive-prompt) and add the code from this section to the `boot.py`. When you restart your ESP32, you will be able to connect to it using WebREPL.

You don't need to install a WebREPL client on your computer to connect to your ESP32. You can go here: http://micropython.org/webrepl **Note that this is an http:// connection. You can't connect to the ESP32 using an encrypted https:// connection.**

If you have multicast DNS enabled, you can connect to your esp32 by entering

# Running files using `import`

If you have the REPL prompt open, you can run a file simply by typing `import filename`. This will cause the entirety of `filename.py` to be executed. However, because the file has been imported, you can't import the file again without rebooting your ESP32. You can, however, work around this. See this thread:

https://forum.micropython.org/viewtopic.php?t=4192