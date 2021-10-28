#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <sys/timerfd.h>

#include "common.c"


int main(int argc, char** argv)
{
	/* Parse arguments */
	if (argc != 3)
	{
		fprintf(stderr, "Usage: %s <dst ip> <src port>:<dsp port>\n", argv[0]);
		return EXIT_FAILURE;
	}

	/* Parse address - distinguish between IPv4 and IPv6 addresses */
	int af_family = AF_INET;
	if (strchr(argv[1], ':') != NULL)
		af_family = AF_INET6;

	union {
		struct sockaddr_in v4;
		struct sockaddr_in6 v6;
	} src_addr, dst_addr;

	memset(&src_addr, 0, sizeof(dst_addr));
	memset(&dst_addr, 0, sizeof(dst_addr));

	int ret;
	if (af_family == AF_INET)
		ret = inet_pton(af_family, argv[1], (void*) &dst_addr.v4.sin_addr);
	else
		ret = inet_pton(af_family, argv[1], (void*) &dst_addr.v6.sin6_addr);

	if (ret != 1)
	{
		fprintf(stderr, "Invalid destination IPv4/IPv6 address\n");
		return EXIT_FAILURE;
	}

    /* Parse ports */
	const char* p1 = argv[2];
	size_t p_len = strlen(p1);
	const char* p2 = strchr(p1, ':');
	if (!p2)
	{
		fprintf(stderr, "Port description must be of the form <src port>:<dst port>\n");
		return EXIT_FAILURE;
	}

	p2++;
	if (p2 > p1 + p_len)
	{
		fprintf(stderr, "Invalid port description\n");
		return EXIT_FAILURE;
	}

	size_t p1_len = p2 - p1 - 1;
	size_t p2_len = (p1 + p_len) - p2;

	if (p1_len == 0 || p2_len == 0)
	{
		fprintf(stderr, "Src and dst ports must not be empty.\n");
		return EXIT_FAILURE;
	}

	int src_port = read_unsigned_int(p1, p1_len);
	int dst_port = read_unsigned_int(p2, p2_len);
	if (src_port <= 0 || dst_port <= 0 || src_port > 65535 || dst_port > 65535)
	{
		fprintf(stderr, "Invalid port specification\n");
		return EXIT_FAILURE;
	}

	if (af_family == AF_INET)
	{
		src_addr.v4.sin_family = AF_INET;
		src_addr.v4.sin_addr.s_addr = INADDR_ANY;
		src_addr.v4.sin_port = htons(src_port);

		dst_addr.v4.sin_family = AF_INET;
		dst_addr.v4.sin_port = htons(dst_port);
	}
	else
	{
		src_addr.v6.sin6_family = AF_INET6;
		src_addr.v6.sin6_addr = in6addr_any;
		src_addr.v6.sin6_port = htons(src_port);

		dst_addr.v6.sin6_family = AF_INET6;
		dst_addr.v6.sin6_port = htons(dst_port);
	}


	/* Create socket */
	int sock = socket(af_family, SOCK_DGRAM, 0);
	if (sock < 0)
	{
		perror("Failed to create socket");
		return EXIT_FAILURE;
	}

	/* Bind socket to src port */
	if (af_family == AF_INET)
		ret = bind(sock, (const struct sockaddr*) &src_addr.v4, sizeof(src_addr.v4));
	else
		ret = bind(sock, (const struct sockaddr*) &src_addr.v6, sizeof(src_addr.v6));

	if (ret < 0)
	{
		perror("Failed to bind socket to src port");
		return EXIT_FAILURE;
	}

	/* Send buffer */
	const char* snd_buf = "Testdata";

	/* Create timer fd */
	int timer_fd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC);
	if (timer_fd < 0)
	{
		perror("Failed to create timer");
		return EXIT_FAILURE;
	}

	struct itimerspec interval;
	interval.it_interval.tv_sec = 1;
	interval.it_interval.tv_nsec = 0;
	interval.it_value.tv_sec = 0;
	interval.it_value.tv_nsec = 1;

	if (timerfd_settime(timer_fd, 0, &interval, NULL) < 0)
	{
		perror("Failed to start timer");
		return EXIT_FAILURE;
	}

	/* Send packets once per second */
	for (;;)
	{
		char buf[8];
		if (read(timer_fd, &buf, 8) != 8)
		{
			perror("Failed to wait for timer");
			return EXIT_FAILURE;
		}

		/* Send packet */
		ssize_t send_ret;
		if (af_family == AF_INET)
		{
			send_ret = sendto(sock, snd_buf, sizeof(snd_buf), 0,
					(const struct sockaddr*) &dst_addr.v4, sizeof(dst_addr.v4));
		}
		else
		{
			send_ret = sendto(sock, snd_buf, sizeof(snd_buf), 0,
					(const struct sockaddr*) &dst_addr.v6, sizeof(dst_addr.v6));
		}

		if (send_ret != sizeof(snd_buf))
		{
			perror("Failed to send packet");
			return EXIT_FAILURE;
		}
	}
}
