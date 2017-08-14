import sys
import socket
import select

def client(user, server, port):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		server_socket.connect((server, int(port)))
		login_token = "LOGIN %s" % user
		server_socket.send(login_token.encode('utf-8'))
	except Exception as e:
		# print(e) debug reason
		print("unable to connect to %s:%s" % (server, port))
		return
	prompt = "%s@%s" % (user, server)
	SOCKETS = [sys.stdin, server_socket]
	#sys.stdout.write("%s >" % prompt); sys.stdout.flush()
	while True:
		sys.stdout.write("%s >" % prompt); sys.stdout.flush()
		read, write, error = select.select(SOCKETS, [], [])

		for sock in read:
			if sock == server_socket:
				data = sock.recv(4096)
				if not data:
					print("\n" + "-"*40)
					print("Server disconnected")
					print("-"*40)
					sock.close()
					return
				else:
					sys.stdout.flush()
					sys.stdout.write('\n')
					sys.stdout.write(data.decode('utf-8'))
					sys.stdout.flush()
			else:
				msg = sys.stdin.readline()
				server_socket.send(msg.encode('utf-8'))
				sys.stdout.flush()
	else:
		server_socket.close()

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print("Pass user, server, port in format 'client.py user host port'.")
		sys.exit(1)
	else:
		client(*sys.argv[1:]) if len(sys.argv) == 4 else client(*sys.argv[1:4])