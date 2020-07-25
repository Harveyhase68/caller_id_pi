# caller_id_pi
Use a USRobotics modem on a Raspberry Pi 1/2/3/4 and identify a line phone caller id and send a POST message to a PHP script. Written in Python 2.7.

Thanks to Pradeep Singh for his contribution of pass_dtmf_digits (https://github.com/pradeesi/pass_dtmf_digits) he wrote the dtmf send digits to a modem, i adapted his code for my purposes, so i'll give back some code for the community.

Use a USB USRobotics USR5637 line modem

Call callerid.py for testing, the script identify the caller id of the caller, send the id to a PHP script. (this can be changed in line 222, replace http://localhost/set.php with whatever you need)

Open rc.local and add (for example)

sudo python /usr/local/sbin/callerid.py &

Don't forget the & at the end of the line, so it will be a process onto another thread, if you forget it, raspberry pi will stop at calling... (is not good)

I adapt the date and time to fit for MySQL, so if you want to have plain what your modem outputs chgange:

Line 214 to sDate = modem_response[5:]

Line 217 to sTime = modem_response[5:]

If you want absolutely no output on command line change

Line 80 to # print "Modem COM Port is: " + com_port

Line 221 to # print("CALL: " + sNumber + " Datum: "+sDate+ " Uhrzeit: "+sTime)

The # sign, starts a comment line

The error messages I would leave a is... Line 80 & 221 are informaton messages, they can be commented out with #

Change line 27 - MODEM_CALL_TIMEOUT = 2 to whatever you like, this is a safety parameter. Do not change it to 0!! Minimum is 1 greater than 10 is not recommended.

You need:

https://requests.readthedocs.io/en/master/

pipenv install requests

No warranty at all, please add your comments in issues or leave a message on office@predl.cc thx
