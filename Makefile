clean:
	rm -rf .cache .eggs .tox *.egg-info
	-find . -type d -name __pycache__ -exec rm -rf {} \;
	find . -type f -name "*.pyc" -exec rm {} \;
	rm -f tests/xml/upnp/IGD.xml
