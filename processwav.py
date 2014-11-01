import wave as wv
import numpy as np
import matplotlib.pyplot as plt
import struct

def wavfetch(filename):
	# Open wav file
	wr = wv.open(filename,'rb')
	# Get params about channel(not used in this instance), sample width (1. about harfone, 2. about audacity edited), 
	# framerate (44100 about audcity and default 10M about hackrf) and frame counts.
	nchannel, sampwidth, framerate, nframes = wr.getparams()[:4]	
	print "channel: %d"%nchannel
	print "sample width: %d"%sampwidth
	print "frame rate: %d"%framerate
	print "frame count: %d"%nframes
	# Get RAW data about wav
	rawdat = wr.readframes(nframes)
	
	# Change the 8bit / 16bit data, the audacity's wav is 16bit and hackrf's data is 8bit.
	dat = []
	if (sampwidth == 1):
		for i in range(0, nframes):
			dat.append(struct.unpack("<b", rawdat[i])[0])
	elif (sampwidth == 2):
		for i in range(0, nframes / 2 - 1):
			dat.append(struct.unpack("<h", rawdat[2*i:2*i+2])[0])
	else:
		print "Unsupport Width, Exit!"
		exit()
	
	wr.close()
	return nchannel, sampwidth, framerate, nframes, dat

# Display the WAV Graphic
def wavdisp(framerate, data):
	count = len(data)
	time = np.arange(0, count)*(1.0/framerate)
	plt.plot(time, data)
	plt.show()
	return

def prewavprocess(framerate, dat):
	# Change the array to np.array
	datsort = np.array(dat)
	# Statictics the wav to calc the MIN level, MAX level and stable start level
	hist, bins = np.histogram(datsort)
	#print hist
	#print bins
	minlevel = int(bins[1]) - 1
	maxlevel = int(bins[9]) + 1
	beginlevel = int(bins[9]) - int(bins[7])
	#print minlevel, maxlevel, beginlevel
	plt.plot(bins[:10], hist)
	plt.show()

	# Find the begin frame of the wav
	beginx = 0
	# if the framerate > 44100 the wav shoud be made by hackrf
	# so need sub the start noise.
	# stable time = 0.01s
	stabletime = 0.01
	if (framerate > 44100):
		countlimited = int(stabletime * framerate)
		#print "limited :", countlimited
		for beginx in range(countlimited, len(dat) - 1):
			if (dat[beginx + 1] - dat[beginx] > beginlevel):
				beginx += 1
				break
	else:
		for beginx in range(0, len(dat) - 1):
			if (dat[beginx] > maxlevel):
				break

	print "begin from: ", beginx

	# Find the end frame of the wav
	endx = 0
	# deley the end time block the end '0'
	delaytime = 0.001
	for endx in range(len(dat) - 1, beginx, -1):
		if (dat[endx] > maxlevel):
			endx += int(delaytime * framerate)
			if (endx > len(dat)):
				endx = len(dat)
			break

	print "end at: ", endx
	return minlevel, maxlevel, beginx, endx

def wavprocess(minlevel, maxlevel, begin, end, framerate, dat):
	# Calc the Frame span
	time = np.arange(0, end - begin)*(1.0/framerate)
	plt.plot(time, dat[begin:end])
	plt.show()

	# Crop the wav
	nframes = end - begin
	dat = dat[begin:end]

	# Memorize the reverse point
	invert = []
	tmp = 0
	for i in range(0, nframes):
		if (dat[i] > maxlevel):
			if (tmp == 0):
				#print i,dat[i]
				invert.append(i)
				tmp = 1
		if (dat[i] < minlevel):
			if (tmp == 1):
				#print i,dat[i]
				invert.append(i)
				tmp = 0
	#print "invert time = ", invert
	
	# Calc the invert span
	span = []
	for i in range(0, (len(invert) - 1)):
		span.append(invert[i+1] - invert[i])
	
	#print span
	#print "span length: ", len(span)
	
	# Find the min span as the standard distance
	# Using 500 samples avoid the long distance
	if (len(span) < 500):
		spansample = span
	else:
		spansample = span[:500]

	spansort = np.array(spansample)
	hist, bins = np.histogram(spansort)
	print hist
	print bins
	plt.plot(bins[:10], hist)
	plt.show()
	
	minspan = bins[0]
	framespantick = int(bins[10]/minspan)

	tmp = 0
	hexline = 0
	hexlen = 0
	hexresult = []
	avespan = minspan
	aveframespan = framespantick
	for i in range(0, (len(span) - 1)):
		tick = int(span[i] / minspan)
		avespan = (avespan + span[i]) / (tick + 1)
		if (tick < framespantick):
			if (tmp == 0):
				tmp = 1
			else:
				tmp = 0
			for j in range(0, tick):
				hexline = (hexline << 1) + (tmp)
				hexlen += 1
		else:
			aveframespan = (aveframespan + tick) / 2
			fill = 4 - hexlen%4
			for j in range(0, fill):
				hexline = hexline << 1
			tmp = 0
			hexresult.append("%x"%hexline)
			hexline = 0
			hexlen = 0

	freq = 1 / avespan * framerate
	framespan = (1. / framerate) * aveframespan * 1000
	return freq, framespan, hexresult

if __name__=="__main__":
	wp = raw_input ("wav file path:")
	print wp
	if (len(wp) == 0):
		#wp = "/home/zhoujustin/unlock.wav"
		wp = "/tmp/tmpam.wav"

	nchannel, sampwidth, framerate, nframes, dat = wavfetch(wp)

	wavdisp(framerate, dat)

	minthreshold, maxthreshold, begin, end= prewavprocess(framerate, dat)
	beginframe = begin
	endframe = end
	minhold = int(minthreshold)
	maxhold = int(maxthreshold)

	freq, framespan, hexresult = wavprocess(minhold, maxhold, beginframe, endframe, framerate, dat)
	print "The Result is "
	print "freq = ", freq
	print "frame span = ", framespan
	for i in range(0, len(hexresult)):
		result = ""
		for j in range(0, len(hexresult[i]) / 2):
			result += hexresult[i][2 * j] + hexresult[i][2 * j + 1] + " "
		print "frame %d : %s"%(i, result)
	exit()




