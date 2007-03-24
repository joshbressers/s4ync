all: s3tool.1 s4ync.1

s3tool.1: s3tool.pod
	pod2man s3tool.pod > s3tool.1

s4ync.1: s4ync.pod
	pod2man s4ync.pod > s4ync.1

clean:
	rm -f s3tool.1 s4ync.1
