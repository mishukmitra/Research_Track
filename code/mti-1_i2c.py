# For good man )))
#
# Links:
# https://base.xsens.com/hc/en-us/articles/115002856865-Best-practices-I2C-and-SPI-for-MTi-1-series?mobile_site=true
# https://onedrive.live.com/view.aspx?cid=AFBE4753126942AB&authKey=%21AFCOFAye1R9aSEc&resid=AFBE4753126942AB%219573&ithint=%2Epdf&open=true&app=WordPdf
# https://onedrive.live.com/view.aspx?cid=AFBE4753126942AB&authKey=%21AFCOFAye1R9aSEc&resid=AFBE4753126942AB%216541&ithint=%2Epdf&open=true&app=WordPdf
#
# We need setup raspberry to use i2c with speed 400kbps. 
#  1. open lxterminal
#  2. type: sudo nano /boot/config.txt
#  3. add line: i2c_arm_baudrate=400000
#  4. save and close file: ctrl+x, y, enter
#
# To run this program type in lxterminal: "sudo python i2c.py"  or "sudo python i2c.py >> /dev/null &" if do not need to see output
# Values from sensor will save in file: "/home/pi/data.txt". Use to see values next command: "tail -f /home/pi/data.txt" 



import time						# this is for make dalay (sleep) 
import io						
import fcntl					# This module performs file control and I/O control on file descriptors.
import sys
import struct					# for make float from 4 byte
import os
from datetime import datetime  	# we will write time to file 

adr=0x6b;						# address of sensors in i2c bus
I2C_SLAVE=0x0703;  				# this used in ioctl. from linux/i2c-dev.h

class i2c:						# create class for working i2c, we work with it like with file, because library SMBus can not read and write array mare than 32 bytes, but we need read and write array more than 32 bytes
	def __init__(self, device, bus):
		self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0) # create description for read
		self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0) # create description for write
		fcntl.ioctl(self.fr, I2C_SLAVE, device) # speak that it I2C SLAVE device
		fcntl.ioctl(self.fw, I2C_SLAVE, device) # speak that it I2C SLAVE device
	def read(self, count):
		return self.fr.read(count) 	# read data from i2c file
	def write(self, data):
		if type(data) is list:
			data = bytearray(data)
		elif type(data) is str:
			data = _b(data)
		self.fw.write(data)			# read data from i2c file	
	def close(self):
		self.fr.close()				# close two i2c files
		self.fw.close()

# The program starts from here		
dev = i2c(adr,1)			# open i2c bus
#dev.write([2,12]) 		   	# config DRDY
dev.write([3, 64, 0, 193]) 	# Send "reset (0x40)" to ControlPipe. 0 - lenght of parameters. 193 - check sum for this message 
time.sleep(1)			   	# mti-1 needs time after reset, wait 1 secomd
#dev.write([3,36,0,221])   	# runselftest
#dev.write([3, 14,0, 243]) 	# restoretodef
for i in range(300): 	   	# in this loop we must read notifications from sensor. when we catch 62 (0x3E) (WakeUp) - it means that sensor was reset and boot
	pipes_len=0		# lenght for notification
	pipem_len=0		# lenght for measures
	try:
		dev.write([4])		# we work with PipeStatus(4) to know how many bytes we must read (3th link page 11)
		s = dev.read(4) 	# now we read 4 bytes to know lenght of massages.
		t = bytearray()		# create new empy array of bytes
       		t.extend(map(ord, s)) # S is string, byt we need bytes
       		pipes_len=t[0]+(t[1]*256); # 1st and 2nd byte are lenght of  NotificationPipe
        	pipem_len=t[2]+(t[3]*256); # 3th and 4th byte are lenght of  MeasurementPipe
		dev.write([5])		# we work with NotificationPipe(5) (3th link page 11)
        	s = dev.read(pipes_len); # read NotificationPipe
        	t = bytearray()	# create new empy array of bytes
        	t.extend(map(ord, s))	# S is string, byt we need bytes
		print(hex(t[0]))	# print MID from notification
		if (t[0]==62):		# if it 0x3E WakeUp	then goto from this loop
			print("WakeUp catched")
			break;
		dev.write([6])		# we work with MeasurementPipe(6) (3th link page 11)
		s=dev.read(pipem_len) # read MeasurementPipe, but we need this Measure, just read
	except:
		print("E")
	time.sleep(0.1)
time.sleep(0.1)
dev.write([3,48,0,209])  # doto Config mode
time.sleep(0.1)
#dev.write([3,192,0,65]) # readconfig
# set configuration for sensor: Acc, Gyr, Mag refresh 1 time in 1 second
dev.write([3,192,24,0x10,0x20,0xff,0xff,0x10,0x60,0xff,0xff,0x40,0x20,0,1,0x80,0x20,0,1,0xc0,0x20,0,1,0xe0,0x20,0xff,0xff,172])
time.sleep(0.1)
dev.write([3,16,0,241])  # goto measure mode
#dev.write([3,63,0,194]) #wakeupAck

# infinity loop
while True:
	time.sleep(0.24) # we read PipeStatus 4 time in second
	#--------------------
	s="";
	pipes_len=0
	pipem_len=0
	try:
		dev.write([4])		# we work with PipeStatus(4) to know how many bytes we must read (3th link page 11)
		s = dev.read(4)		# now we read 4 bytes to know lenght of massages.
		t = bytearray()
		t.extend(map(ord, s))
		#print("\r\n4. PipeStatus: %x %x   %x %x" %(t[0], t[1], t[2], t[3]));
		pipes_len=t[0]+(t[1]*256);
		pipem_len=t[2]+(t[3]*256);
	except:
		print("error")
	if (pipes_len>0):
		print "\r\n5. Notification: ",
		dev.write([5])				# we work with NotificationPipe(5) (3th link page 11)
		s = dev.read(pipes_len);	# read NotificationPipe
		t = bytearray()
		t.extend(map(ord, s))
		for i in range(pipes_len):	# print Notification
			print hex(t[i]),
	pipen_len=0
	if (pipem_len>0):
		dev.write([6])				# we work with MeasurementPipe(6) (3th link page 11)
		s =  dev.read(pipem_len)	# read MeasurementPipe
		t = bytearray()
		t.extend(map(ord, s))
		sum=0
		for i in range(pipem_len):  # make checkSum of message
			sum=sum+t[i];
		if ((sum%256)==1):			# and check it
			print("CheckSum is correct")
		if (t[0]==0x36):			# MtData2 is MID 0x36, we need it
			print(chr(27) + "[2J")	# clear output
			print("\r\nWe have MtData2 message")
			zf=open("/home/pi/data.txt", 'a')	# open file to save values
			zf.write(str(datetime.now())+"\r\n")# write data and time to file
			#-------------------
			k=2; # k is our position of bytes in message
			while (k<t[1]): # read byte after byte if it more than lenght in message
				xdi=t[k]*256+t[k+1];	# make XDI from 2 bytes
				k=k+1;
				if (xdi == 0x1020):   	#  0x1020 = PacketCounter
					cnt=t[k+2]*256+t[k+3]
					print("PacketCounter = "+str(cnt))
					k=k+4
				elif (xdi == 0x1060):	#  0x1060 = Sample time fine
					print("Sample time fine")
					k=k+6
				elif (xdi == 0x2010):	#  0x2010 = Quaternion
					print("Quaternion: not need")
					k=k+18
				elif (xdi == 0x8030):	#  0x8030 = DeltaQ
					print("DeltaQ: not need")
					k=k+18
				elif (xdi == 0xe020):	#  0xe020 = Status word (4 bytes)
					w=t[k+2]*256*256*256+t[k+3]*256*256+t[k+4]*256+t[k+5];
					print("Status word: "+hex(w))
					k=k+6
					zf.close() 			# close file because it is last field
				elif (xdi == 0xc020):	#  0xc020 = Magnetic
					k=k+1
					dd1 = bytearray([t[k+1], t[k+2], t[k+3], t[k+4]])
					d1= struct.unpack('>f', dd1)  	# make float from bytes array
					dd2 = bytearray([t[k+5], t[k+6], t[k+7], t[k+8]])
					d2= struct.unpack('>f', dd2)	# make float from bytes array	
					dd3 = bytearray([t[k+9], t[k+10], t[k+11], t[k+12]])
					d3= struct.unpack('>f', dd3)  	# make float from bytes array
					print("Magnetic: "+str(d1)+"   "+str(d2)+"   "+str(d3))				# print to output
					zf.write("Magnetic: "+str(d1)+"   "+str(d2)+"   "+str(d3)+"\r\n")	# print to file
					k=k+13
				elif (xdi == 0x4020):	#  0x4020 = Acceleration 
					k=k+1
					dd1 = bytearray([t[k+1], t[k+2], t[k+3], t[k+4]])
					d1= struct.unpack('>f', dd1)  	# make float from bytes array
					dd2 = bytearray([t[k+5], t[k+6], t[k+7], t[k+8]])
					d2= struct.unpack('>f', dd2)  	# make float from bytes array
					dd3 = bytearray([t[k+9], t[k+10], t[k+11], t[k+12]])
					d3= struct.unpack('>f', dd3)  	# make float from bytes array
					print("Acceleration: "+str(d1)+" "+str(d2)+" "+str(d3))				 # print to output
					zf.write("Acceleration: "+str(d1)+"   "+str(d2)+"   "+str(d3)+"\r\n")# print to file
					k=k+13
				elif (xdi == 0x8020):	#  0x8020 = RateOfTurn
					k=k+1
					dd1 = bytearray([t[k+1], t[k+2], t[k+3], t[k+4]])
					d1= struct.unpack('>f', dd1)  	# make float from bytes array
					dd2 = bytearray([t[k+5], t[k+6], t[k+7], t[k+8]])
					d2= struct.unpack('>f', dd2)  	# make float from bytes array
					dd3 = bytearray([t[k+9], t[k+10], t[k+11], t[k+12]])
					d3= struct.unpack('>f', dd3)  	# make float from bytes array
					print("RateOfTurn: "+str(d1)+" "+str(d2)+" "+str(d3))				# print to output
					zf.write("RateOfTurn: "+str(d1)+"   "+str(d2)+"   "+str(d3)+"\r\n") # print to file
					k=k+13
				elif (xdi == 0x4010):	#  0x4010 = DeltaV
					print("DeltaV: not need")
					k=k+14
				else:
					print("unknown xdi: "+hex(xdi))
		#-----------------------------
dev.close()

es we must read (3th link page 11)
		s = dev.read(4)		# now we read 4 bytes to know lenght of massages.
		t = bytearray()
		t.extend(map(ord, s))
		#print("\r\n4. PipeStatus: %x %x   %x %x" %(t[0], t[1], t[2], t[3]));
		pipes_len=t[0]+(t[1]*256);
		pipem_len=t[2]+(t[3]*256);
	except:
		print("error")
	if (pipes_len>0):
		print "\r\n5. Notification: ",
		dev.write([5])				# we work with NotificationPipe(5) (3th link page 11)
		s = dev.read(pipes_len);	# read NotificationPipe
		t = bytearray()
		t.extend(map(ord, s))
		for i in range(pipes_len):	# print Notification
			print hex(t[i]),
	pipen_len=0
	if (pipem_len>0):
		dev.write([6])				# we work with MeasurementPipe(6) (3th link page 11)
		s =  dev.read(pipem_len)	# read MeasurementPipe
		t = bytearray()
		t.extend(map(ord, s))
		sum=0
		for i in range(pipem_len):  # make checkSum of message
			sum=sum+t[i];
		if ((sum%256)==1):			# and check it
			print("CheckSum is correct")
		if (t[0]==0x36):			# MtData2 is MID 0x36, we need it
			print(chr(27) + "[2J")	# clear output
			print("\r\nWe have MtData2 message")
			zf=open("/home/pi/data.txt", 'a')	# open file to save values
			zf.write(str(datetime.now())+"\r\n")# write data and time to file

		#-------------------
		k=2; # k is our position of bytes in message
		while (k<t[1]): # read byte after byte if it more than lenght in message
			xdi=t[k]*256+t[k+1];	# make XDI from 2 bytes
			k=k+1;
			if (xdi == 0x1020):   	#  0x1020 = PacketCounter
				cnt=t[k+2]*256+t[k+3]
				print("PacketCounter = "+str(cnt))
				k=k+4
			elif (xdi == 0x1060):	#  0x1060 = Sample time fine
				print("Sample time fine")
				k=k+6
			elif (xdi == 0x2010):	#  0x2010 = Quaternion
				print("Quaternion: not need")
				k=k+18
			elif (xdi == 0x8030):	#  0x8030 = DeltaQ
				print("DeltaQ: not need")
				k=k+18
			elif (xdi == 0xe020):	#  0xe020 = Status word (4 bytes)
				w=t[k+2]*256*256*256+t[k+3]*256*256+t[k+4]*256+t[k+5];
				print("Status word: "+hex(w))
				k=k+6
				zf.close() 			# close file because it is last field
			elif (xdi == 0xc020):	#  0xc020 = Magnetic
				k=k+1
				dd1 = bytearray([t[k+1], t[k+2], t[k+3], t[k+4]])
				d1= struct.unpack('>f', dd1)  	# make float from bytes array
				dd2 = bytearray([t[k+5], t[k+6], t[k+7], t[k+8]])
				d2= struct.unpack('>f', dd2)	# make float from bytes array	
				dd3 = bytearray([t[k+9], t[k+10], t[k+11], t[k+12]])
				d3= struct.unpack('>f', dd3)  	# make float from bytes array
				print("Magnetic: "+str(d1)+"   "+str(d2)+"   "+str(d3))				# print to output
				zf.write("Magnetic: "+str(d1)+"   "+str(d2)+"   "+str(d3)+"\r\n")	# print to file
				k=k+13
			elif (xdi == 0x4020):	#  0x4020 = Acceleration 
				k=k+1
				dd1 = bytearray([t[k+1], t[k+2], t[k+3], t[k+4]])
				d1= struct.unpack('>f', dd1)  	# make float from bytes array
				dd2 = bytearray([t[k+5], t[k+6], t[k+7], t[k+8]])
				d2= struct.unpack('>f', dd2)  	# make float from bytes array
				dd3 = bytearray([t[k+9], t[k+10], t[k+11], t[k+12]])
				d3= struct.unpack('>f', dd3)  	# make float from bytes array
				print("Acceleration: "+str(d1)+" "+str(d2)+" "+str(d3))				 # print to output
				zf.write("Acceleration: "+str(d1)+"   "+str(d2)+"   "+str(d3)+"\r\n")# print to file
				k=k+13
			elif (xdi == 0x8020):	#  0x8020 = RateOfTurn
				k=k+1
				dd1 = bytearray([t[k+1], t[k+2], t[k+3], t[k+4]])
				d1= struct.unpack('>f', dd1)  	# make float from bytes array
				dd2 = bytearray([t[k+5], t[k+6], t[k+7], t[k+8]])
				d2= struct.unpack('>f', dd2)  	# 