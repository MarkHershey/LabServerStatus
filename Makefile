REMOVE = rm -rvf
RUN = bash

all:
	black .
clean:
	$(REMOVE) logs
	$(REMOVE) ./**/logs
	$(REMOVE) tmp_*.txt
	$(REMOVE) ./**/tmp_*.txt
	$(REMOVE) __pycache__
	$(REMOVE) ./**/__pycache__