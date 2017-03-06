#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
streamscrobbler is originaly created by Håkan Nylén, https://github.com/confact
and ported to python3 by Rodrigo Gomes, https://github.com/rodgomesc

for more info:
https://github.com/Dirble/streamscrobbler-python
'''


__doc__='''

def load_src(name, fpath):
    import os, imp
    p = fpath if os.path.isabs(fpath) \
        else os.path.join(os.path.dirname(__file__), fpath)
    return imp.load_source(name, p)

load_src('streamscrobbler','streamscrobbler_port_python3.py')
from streamscrobbler import streamscrobbler
streamscrobbler = streamscrobbler()


##streamurl can be a url directly to the stream or to a pls file. Support for m3u is coming soon.
streamurl = "http://217.198.148.101:80/"
stationinfo = streamscrobbler.getServerInfo(streamurl)
##metadata is the bitrate and current song
metadata = stationinfo.get("metadata")
## status is the integer to tell if the server is up or down, 0 means down, 1 up, 2 means up but also got metadata.
status = stationinfo.get("status")

'''
import re
import urllib.request
import sys

class streamscrobbler:
    def parse_headers(self, response):

        sys.exit(1)
        headers = {}
        int = 0
        while True:
            line = response.readline()
            if line == '\r\n':
                break  # end of headers
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key] = value.rstrip()
            if int == 12:
                break;
            int = int + 1
        return headers


    def getServerInfo(self, url):
        if url.endswith('.pls') or url.endswith('listen.pls?sid=1'):
            address = self.checkPLS(url)
        else:
            address = url

        if isinstance(address, str):
            meta_interval = self.getAllData(address)

        else:
            meta_interval = {"status": 0, "metadata": None}

        return meta_interval
   
    def getAllData(self, address):
        shoutcast = False
        status = 0
        request = urllib.request.Request(address)
        user_agent = 'iTunes/9.1.1'
        request.add_header('User-Agent', user_agent)
        request.add_header('icy-metadata', 1)

        response = urllib.request.urlopen(request, timeout=6)
        headers = self.getHeaders(response)

        if "Server" in headers:
            shoutcast = headers['Server']
        elif "X-Powered-By" in headers:
            shoutcast = headers['X-Powered-By']
        elif "icy-notice1" in headers:
            shoutcast = headers['icy-notice2']
        else:
            shoutcast = bool(1)

        if isinstance(shoutcast, bool):
            if shoutcast is True:
                status = 1
            else:
                status = 0
            metadata = False;
        elif "SHOUTcast" in shoutcast:
            status = 1
            metadata = self.shoutcastCheck(response, headers, False)
        elif "Icecast" or "137" in shoutcast:
            status = 1
            metadata = self.shoutcastCheck(response, headers, True)
        elif "StreamMachine" in shoutcast:
            status = 1
            metadata = self.shoutcastCheck(response, headers, True)
        elif shoutcast is not None:
            status = 1
            metadata = self.shoutcastCheck(response, headers, True)
        else:
            metadata = False
        response.close()
        if "content-length" in headers:
            return {"status": status, "metadata": metadata,"content-length":headers["content-length"]}
        else:
            return {"status": status, "metadata": metadata}

    ##FUNCAO CORRIGIDA
    def checkPLS(self, address):
        try:
            response = urllib.request.urlopen(address, timeout=2)
            temp = response.read().decode('utf-8').split('\n')
            for line in temp:
                if line.startswith("File1="):
                    stream = line;

            response.close()
            if 'stream' in locals():
                return stream[6:]
            else:
                return bool(0)
        except Exception:
            return bool(0)


    def shoutcastCheck(self, response, headers, itsOld):
        if itsOld is not True:
            if 'icy-br' in headers:
                bitrate = headers['icy-br']
                bitrate = bitrate.rstrip()
            else:
                bitrate = None

            if 'icy-metaint' in headers:
                icy_metaint_header = headers['icy-metaint']
            else:
                icy_metaint_header = None

            if "Content-Type" in headers:
                contenttype = headers['Content-Type']
            elif 'content-type' in headers:
                contenttype = headers['content-type']

        else:
            if 'icy-br' in headers:
                bitrate = headers['icy-br'].split(",")[0]
            else:
                bitrate = None
            if 'icy-metaint' in headers:
                icy_metaint_header = headers['icy-metaint']
            else:
                icy_metaint_header = None

        if headers.get('Content-Type') is not None:
            contenttype = headers.get('Content-Type')
        elif headers.get('content-type') is not None:
            contenttype = headers.get('content-type')



        if icy_metaint_header is not None:
            metaint = int(icy_metaint_header)

            read_buffer = metaint + 255
            content = response.read(read_buffer).decode('UTF-8', 'ignore')
            start = "StreamTitle='"
            end = "';"


            title = re.search('%s(.*)%s' % (start, end), content).group(1)
            title = re.sub("StreamUrl='.*?';", "", title).replace("';", "").replace("StreamUrl='", "")
            title = re.sub("&artist=.*", "", title)
            title = re.sub("http://.*", "", title)
            title.rstrip()

            return {'song': title, 'bitrate': bitrate, 'contenttype': contenttype.rstrip()}
        else:
            return False

    def getHeaders(self, response):

        if self.is_empty(dict(response.info())) is False:
            headers = dict(response.info())
        elif hasattr(response.info(),"item") and self.is_empty(response.info().item()) is False:
            headers = response.info().item()
        else:
            headers = self.parse_headers(response)

        return headers

    def is_empty(self, any_structure):
        if any_structure:
            return False
        else:
            return True

    def stripTags(self, text):
        finished = 0
        while not finished:
            finished = 1
            start = text.find("<")
            if start >= 0:
                stop = text[start:].find(">")
                if stop >= 0:
                    text = text[:start] + text[start + stop + 1:]
                    finished = 0
        return text
