import sys
import socket

# usage message
def usage():
    print("Usage: CruzIDMyCurl.py [http://hostname:port | http://ipaddress:port hostname].")
    sys.exit()

# check number of command line args
argc = len(sys.argv)
if (argc < 2 or argc > 3):
    print("Error: Incorrect number of arguments.")
    usage()

# needs to be http://
if not sys.argv[1].startswith('http://'):
    print("curl: HTTPS not supported")
    usage()

# default port
port = 80
temp = 0
temp2 = 0
path = ' '
host = ''

# handle http://hostname:port or http://hostname/path or http:hostname:port/path

# user inputted port number
# url of for http://host:port or http://host:port/path
temp = sys.argv[1].find(':', 7) 
if temp != -1:
    # url of type http://host:port/path
    temp2 = sys.argv[1].find('/', temp)
    if temp2 != -1:
        try:
            port = int(sys.argv[1][temp+1:temp2])
        except:
            print("Invalid port number.")
            usage()

        # store path
        path = sys.argv[1][temp2+1:]
        path = path + ' ' 
        host = sys.argv[1][7:temp]

    # url of form http://host:port
    else:
        try:
            port = int(sys.argv[1][temp+1:])
            host = sys.argv[1][7:temp]
        except:
            print("Invalid port number.")
            usage()

# user does not specify port number
# url of type http://hostname or http://hostname/path
elif temp == -1:
    temp = sys.argv[1].find('/', 7) 

    # url of type http://hostname
    if temp == -1:
        host = sys.argv[1][7:]
    
    # url of type http://hostname/path
    else:
        path = sys.argv[1][temp+1:]
        path = path + ' ' 
        host = sys.argv[1][7:temp]
    

ipaddr = ''

# handle ip addresses
if (argc == 3):

    # swap ip addr and hostname
    ipaddr, host = host, sys.argv[2]

# some socket refs are from https://realpython.com/python-sockets/ 

# make a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)          # make TCP socket

# connect to the server
try:
    s.connect((host, port))                                        # bind for servers, connect client
except:
    print("curl: Could not resolve host")
    usage()


# request/query the server
reqq = "GET /" + path + "HTTP/1.1\r\nHost: " + host + "\r\n\r\n"
#print(reqq)
s.sendall(reqq.encode())

# write to log file
def write_log(successful, host, path, hostname, srcIP, dstIP, srcPort, dstPort, respLine):
    file = open('Log.csv', 'a')

    # successful or not, requested url, hostname, srcIP, dstIP, srcPort, dstPort, respLine 
    file.write("Query: " + str(successful) + ", Requested URL: http://" + str(host) + "/" + str(path) + ", Hostname: " + str(hostname) + ", Source IP: " + str(srcIP) + ", Destination IP: " + str(dstIP) + ", Source Port: " + str(srcPort) + ", Destination Port: " + str(dstPort) + ", Response Line: " + str(respLine) + ". \n")

    file.close()

# for log file
hostnamee = socket.gethostname()
destinIP = socket.gethostbyname(hostnamee)
sourcePort = s.getsockname()[1]
sourceIP = s.getsockname()[0]
destinPort = port

# receive data
try:
    resp = s.recv(1024).decode()
    #print(resp)
    #print(resp.encode('utf-8'))

# use of 443 or other unusable port
except Exception as e:
    if port == 443:
        print("curl: Connection reset by peer")
    else:
        print("Socket Connection Error: Cannot get server response (use a different port).")

    write_log("Unsuccessful", host, path, str(hostnamee), str(sourceIP), str(destinIP), str(sourcePort), str(destinPort), str(e))
    s.close()
    usage()

# get response line
rtmp = resp.find('\n', 0) 
responLine = resp[0:rtmp]
#print(responLine)

# no issues codes 100-299 are considered success
if resp.startswith("HTTP/1.1 2") or resp.startswith("HTTP/1.1 1"):
    write_log("Successful", host, path, str(hostnamee), str(sourceIP), str(destinIP), str(sourcePort), str(destinPort), responLine)
else:
    write_log("Unsuccessful", host, path, str(hostnamee), str(sourceIP), str(destinIP), str(sourcePort), str(destinPort), responLine)

# handle chunk encoding
if not resp.find("Transfer-Encoding: chunked") == -1:
    print("curl: Chunked transfer encoding not supported")
    s.close()
    usage()


# content length not found
clen = "NOT FOUND"

# get length of the content
rtmp = resp.find('Content-Length: ')
if rtmp == -1:
    rtmp = resp.find('content-length: ')

# content length found
if not rtmp == -1:
    rtmp = rtmp+len('Content-Length: ') 
    rtmp2 = resp.find('\n', rtmp)
    clen = int(resp[rtmp:rtmp2])

# successful retrieval (404 downloaded objects are still a success)
rtmp = resp.find('\r\n\r\n')

#file.write(resp[rtmp+4:])                   # +4 to skip writing \r\n\r\n

# workaround to making temp files (cannot do without os module)
final = resp[rtmp+4:].encode()

wrote = len(resp[rtmp+4:])
remaining = 0

# we have content length, download the body
if not clen == "NOT FOUND":
    try:
        remaining = clen - wrote

        while remaining > 0:
            resp = s.recv(1024)
            remaining = remaining - len(resp)
            final += resp

        # write body to httpoutput.html
        file = open('HTTPoutput.html', 'w')
        file.write(str(final))
        file.close()
        s.close()

        print("Successful. Requested URL: http://" + str(host) + "/" + str(path) + ". HTTP response: "+ str(responLine))
        
    except:
        print("Unsuccessful. Requested URL: http://" + str(host) + "/" + str(path)+ ". HTTP response: "+ str(responLine))
        s.close()
        usage()


# content length not provided in the header. write till we are getting response. OR NO HEADER
else:
    try:
        while len(resp) > 0:
            resp = s.recv(1024)
            final += resp

        # write body to httpoutput.html
        file = open('HTTPoutput.html', 'w')
        file.write(str(final))
        file.close()
        s.close()
        
        print("Successful. Requested URL: http://" + host + "/" +path+ ". HTTP response: "+ responLine)

    except:
        print("Unsuccessful. Requested URL: http://" + host + "/" + path+ ". HTTP response: "+ responLine)
        s.close()
        usage()


