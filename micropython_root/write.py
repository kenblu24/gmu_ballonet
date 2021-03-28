"""
Authors: Austin Mulville, Kevin Eckert

These functions allow writing data to files in the esp32 using micropython.
write_raw writes binary data directly, write_data writes in an encoded format. 
"""

def write_raw(filename, raw):
	f = open(filename, 'a') #a for append, w for write (would overwrite the whole file), x for create (however a will create a new file if it does not exist already)
	for i in range(0, len(raw)): #in the length of the data
		a = bytes(raw)
		f.write(a) #this is writing 
		f.write('\n')
	f.close()
	
def write_data(filename, data):
	#Usage: Data is a string. Filename is a string
	f = open(filename, 'a')
	f.write(data + '\n')
	f.close()