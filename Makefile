.PHONY: download

download:
	python biorxivr/download.py 

download-one:
	python biorxivr/download.py $(URL)

upload:
	python biorxivr/upload.py

itemlist.txt:
	curl 'https://archive.org/metamgr.php?f=exportIDs&w_mediatype=texts&w_collection=biorxiv*' > $@

clean: itemlist.txt
	python biorxivr/utils.py clean
