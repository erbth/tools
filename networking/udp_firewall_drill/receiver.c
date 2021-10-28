#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "common.c"


int main(int argc, char** argv)
{
	/* Parse arguments */
	if (argc != 2)
	{
		fprintf(stderr, "Usage: %s <port>\n", argv[0]);
		return EXIT_FAILURE;
	}

	int port = read_unsigned_int(argv[1], strlen(argv[1]));
	if (port <= 0 || port > 65535)
	{
		fprintf(stderr, "Invalid port\n");
		return EXIT_FAILURE;
	}


	/* Create a socket */
	int sock = socket(AF_INET6, SOCK_DGRAM, 0);
	if (sock < 0)
	{
		perror("Failed to create socket");
		return EXIT_FAILURE;
	}

	/* Bind socket to receiving port */
	struct sockaddr_in6 dst_addr;
	memset(&dst_addr, 0, sizeof(dst_addr));

	dst_addr.sin6_family = AF_INET6;
	dst_addr.sin6_port = htons(port);
	dst_addr.sin6_addr = in6addr_any;

	if (bind(sock, (const struct sockaddr*) &dst_addr, sizeof(dst_addr)) < 0)
	{
		perror("Failed to bind socket to receiving port");
		return EXIT_FAILURE;
	}

	/* Receive packets */
	struct sockaddr_in6 src_addr;
	memset(&src_addr, 0, sizeof(src_addr));

	char buffer[1024];

	for (;;)
	{
		socklen_t addrlen = sizeof(src_addr);
		ssize_t recv_ret = recvfrom(sock, &buffer, sizeof(buffer), 0,
				(struct sockaddr*) &src_addr, &addrlen);

		if (recv_ret < 0)
		{
			perror("  Failed to receive packet");
			continue;
		}

		int family = AF_INET6;
		printf("%24s %5d:%d\n",
				inet_ntop(family, (const void*) &src_addr.sin6_addr, buffer, sizeof(buffer)),
				(int) ntohs(src_addr.sin6_port),
				port);
	}
}
