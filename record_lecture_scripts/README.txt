Some details about my setup for recording my lectures
-----------------------------------------------------
* I have Linux on my laptop. My scripts would probably also work on Mac. Some significant work would be needed to get them to work on Windows, but it could be done.
* I use a MOVO WMIC50 lapel mic. I think it produces decent recordings, but I have to recharge the batteries every week. Since I only recently figured this out, several of my recordings have severe audio issues.
* I usually plug my laptop into the podium and set it next to the podium monitor. My display is configured to span two monitors, such that my laptop screen shows me personal notes, and the podium display shows what the students also see on the projector.
* My recording script is written in BASH. It uses a tool named "recordmydesktop" to record the only display screen and the audio. It records in ".ogv" format. When it is done, it automatically uploads the recorded video to one of my servers.
* It has a hotkey to pause the recordings, but I rarely use it.
* If I want to break up a lecture into multiple videos, I can just stop my script and run it again. Or, I can edit the videos later, since they are stored on a server in my office.
* My server automatically runs a BASH script in the background that uses "avconv" to generate smaller low-resolution versions of my videos. (It can conver to ".mp4" or other formats, but I currently have it configured to stay with ".ogv".)
* I serve my videos using Apache2. I installed a plug-in called "Mod-H264-Streaming-Apache-Version2", to stream video formats.
* My class web pages link to a simple PHP page I wrote that displays my recordings and lets the class annotate with timestamps.
* Apache provides simple mechanisms to password-protect the videos. However, since they are currently incomplete and only cover a small portion of the course, I have that turned off.



To set up apache to stream MP4 files
------------------------------------
These instructions are from http://h264.code-shop.com/trac/wiki/Mod-H264-Streaming-Apache-Version2
sudo apt-get install apache2-threaded-dev
cd ~
wget http://h264.code-shop.com/download/apache_mod_h264_streaming-2.2.7.tar.gz
tar -zxvf apache_mod_h264_streaming-2.2.7.tar.gz
cd ~/mod_h264_streaming-2.2.7
./configure --with-apxs=`which apxs2`
make
sudo make install
then, add the following lines to /etc/apache2/apache2.conf:
	LoadModule h264_streaming_module /usr/lib/apache2/modules/mod_h264_streaming.so
	AddHandler h264-streaming.extensions .mp4
sudo /etc/init.d/apache start
