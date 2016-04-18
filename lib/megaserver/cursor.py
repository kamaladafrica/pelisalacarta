import urllib2

class Cursor(object):
    def __init__(self, file):
        self._file=file
        self.pos=0
        self.conn =None

    def mega_request(self,offset, retry=False):
        if not self._file.url or retry:
            if self._file.folder_id :
                file = self._file._client.api_req({"a":"g","g":1,"n":self._file.file_id},"&n="+self._file.folder_id)
                self._file.url= file["g"]
            else:
                file = self._file._client.api_req({'a': 'g', 'g': 1, 'p': self._file.file_id})
                self._file.url= file["g"]

        req = urllib2.Request(self._file.url)
        req.headers['Range'] = 'bytes=%s-' % (offset)
        try:
            self.conn = urllib2.urlopen(req)
            self._file.prepare_decoder(offset)
        except:
            #La url del archivo expira transcurrido un tiempo, si da error 403, reintenta volviendo a solicitar la url mediante la API
            self.mega_request(offset, True)

    def read(self,n=None):
        if not self.conn:
            return
        res=self.conn.read(n)
        if res:
            res = self._file.decode(res)
            self.pos+=len(res)
        return res


    def seek(self,n):
        if n>self._file.size:
            n=self._file.size
        elif n<0:
            raise ValueError('Seeking negative')
        self.mega_request(n)
        self.pos=n

    def tell(self):
        return self.pos

    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_val, exc_tb):
        self._file.cursor =None
