.PHONY: download

download:
	python biorxivr/download.py 

download-one:
	python biorxivr/download.py $(URL)

upload:
	python biorxivr/upload.py

clean:
	python biorxivr/utils.py clean
