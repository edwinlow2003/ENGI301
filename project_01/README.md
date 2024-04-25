# Morse Code Transceiver
## Project Background
This Morse code transceiver allows users to input Morse code with buttons. Users have the option to adjust the pause times between letters and words with a potentiometer. The user can use the blue arcade button to input Morse code. The button will light up and a buzzer will buzz when the user input a dot or a dash (short or long press). The red pushbutton is the delete button in case the user enters a wrong letter. The green pushbutton is the control button for the user to start/stop inputting Morse code. It is also used for transmitting the message if the user presses it for 3 seconds. (As of now, the transmitting function still does not work, so long-pressing the green pushbutton only resets the message string.)

<br/><br/>
## Hardware
For the details of the project's hardware setup, please refer to the hackster.io page here: https://www.hackster.io/el52/engi-301-pocketbeagle-morse-code-transceiver-c5b2f4

<br/><br/>
## Software Build Instructions
### Install Python 3.8.18
On the PocketBeagle, install Python 3.8.18 to run the libraries that the SPI screen uses. Adafruit updated their adafruit-circuitpython-rgb-display library so that Python 3.7 no longer works on it.

Here is a link on how to install Python 3.8: https://stackoverflow.com/questions/62830862/how-to-install-python3-8-on-debian-10
Make sure to replace 3.8.2 on the stackoverflow commands with 3.8.18.

Or, run the following in the PocketBeagle's terminal after the PocketBeagle is connected to Wi-Fi:

```
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev liblzma-dev

curl -O https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tar.xz

tar -xf Python-3.8.18.tar.xz

cd Python-3.8.18
./configure --enable-optimizations --enable-loadable-sqlite-extensions

make -j 1

sudo make altinstall

python3.8 --version
```

The last line should output Python 3.8.18.

<br/><br/>
### Install libraries for the SPI screen
Before running the code, do the following to install libraries for the SPI Screen:

```
sudo apt-get update
sudo python3.8 -m pip install --upgrade Pillow
sudo python3.8 -m pip install -U setuptools
sudo python3.8 -m pip install adafruit-circuitpython-busdevice
sudo python3.8 -m pip install adafruit-circuitpython-rgb-display
sudo apt-get install ttf-dejavu -y
```

<br/><br/>
## Software Operation Instructions
To run the code, do the following:
```
git clone https://github.com/edwinlow2003/ENGI301/tree/main/project_01
cd /var/lib/cloud9/ENGI301/project_01
sudo ./run
```

If ```sudo ./run``` doesn't work, then type ```chmod 755 run``` to change the permission for the run file. This should make the file executable.

<br/><br/>

For the project to run automatically on boot, do the following:
```
sudo crontab -e
@reboot sleep 30 && sh /var/lib/cloud9/ENGI301/project_01/run > /var/lib/cloud9/logs/cronlog 2>&1
```
Restart the PocketBeagle by running ```sudo reboot``` to make sure that it runs automatically on boot.

