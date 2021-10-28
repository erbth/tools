.PHONY: all
all: sender receiver

sender: sender.c common.c
	gcc -Wall -Werror -o $@ $<

receiver: receiver.c common.c
	gcc -Wall -Werror -o $@ $<


.PHONY: clean
clean:
	rm -f sender receiver
