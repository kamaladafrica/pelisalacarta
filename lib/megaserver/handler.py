import BaseHTTPServer
import urlparse
import time
import urllib
import types
import os
import re


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        pass

    def parse_range(self, range):
        if range:
            m=re.compile(r'bytes=(\d+)-').match(range)
            if m:
                try:
                    return int(m.group(1))
                except:
                    pass
        return 0

    def do_GET(self):
        if self.server.request: self.server.request.wfile.close()
        self.server.request = self
        self.server._client.connected = True

        if self.do_HEAD():
            with self.server._client.file.create_cursor(self.offset) as f:
                while True:
                    buf= f.read(1024*16)
                    if buf:
                        self.wfile.write(buf)
                    else:
                        break

    def send_pls(self, files):
        playlist = "[playlist]\n\n"
        for x,f in enumerate(files):
            playlist += "File"+str(x+1)+"=http://" + self.server._client.ip + ":" + str(self.server._client.port) + "/" + urllib.quote(f.name)+"\n"
            playlist += "Title"+str(x+1)+"=" +f.name+"\n"

        playlist +="NumberOfEntries=" + str(len(files))
        playlist +="Version=2"
        self.send_response(200, 'OK')
        self.send_header("Content-Length", str(len(playlist)))
        self.finish_header()
        self.wfile.write(playlist)

    def do_HEAD(self):
        url=urlparse.urlparse(self.path).path

        while not self.server._client.files:
            time.sleep(1)

        if url=="/playlist.pls":
            self.send_pls(self.server._client.files)
            return False


        if not self.server._client.file or urllib.unquote(url)[1:] != self.server._client.file.name:
            for f in self.server._client.files:
                if f.name == urllib.unquote(url)[1:]:
                    self.server._client.file = f
                    break

        if self.server._client.file and urllib.unquote(url)[1:] == self.server._client.file.name:
            self.offset=0
            size, mime = self._file_info()
            range=self.parse_range(self.headers.get('Range', None))
            if range:
                self.offset=range
                range=(range, size-1, size)

            self.send_resp_header(mime, size, range)
            return True

        else:
            self.send_error(404, 'Not Found')

    def _file_info(self):
        size=self.server._client.file.size
        ext=os.path.splitext(self.server._client.file.name)[1]
        mime=self.server._client.VIDEO_EXTS.get(ext)
        if not mime:
            mime='application/octet-stream'
        return size,mime

    def send_resp_header(self, cont_type, cont_length, range=False):
        if range:
            self.send_response(206, 'Partial Content')
        else:
            self.send_response(200, 'OK')

        self.send_header('Content-Type', cont_type)
        self.send_header('transferMode.dlna.org', 'Streaming')
        self.send_header('contentFeatures.dlna.org', 'DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000')
        self.send_header('Accept-Ranges', 'bytes')

        if range:
            if isinstance(range, (types.TupleType, types.ListType)) and len(range)==3:
                self.send_header('Content-Range', 'bytes %d-%d/%d' % range)
                self.send_header('Content-Length', range[1]-range[0]+1)
            else:
                raise ValueError('Invalid range value')
        else:
            self.send_header('Content-Length', cont_length)
        self.finish_header()

    def finish_header(self):
        self.send_header('Connection', 'close')
        self.end_headers()