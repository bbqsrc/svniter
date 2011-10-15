#from collections import OrderedDict
from subprocess import Popen, PIPE
from io import StringIO

import xml.sax
import xml.sax.handler
import datetime


def compatibility_check():
    # XXX: gotta add checks for svn, etc
    return True
if not compatibility_check():
    raise IOError("SVN not found")


class SVNDirectory:
    def get_log(self):
        if self.log:
            return self.log
        
        class Handler(xml.sax.handler.ContentHandler):
            def __init__(self):
                self.out = []
                self.revision = None
                self.tag = None
            
            def startElement(self, name, attr):
                self.tag = name
                
                if name == "logentry":
                    self.revision = int(attr.get("revision"))
                    self.out.append({
                        "revision": self.revision,
                        "author": "",
                        "msg": "",
                        "date": None,
                        "paths": []
                    })
                    
                elif name == "path":
                    self.out[-1]["paths"].append({
                        "path": None,
                        "kind": attr.get("kind"),
                        "action": attr.get("action")
                    })
            
            def characters(self, ch):
                if not ch or ch.strip() == "":
                    return
                
                if self.tag in ("author", "msg"):
                    self.out[-1][self.tag] = ch.strip()
                
                elif self.tag == "path":
                    self.out[-1]["paths"][-1]["path"] = ch.strip()
                
                elif self.tag == "date":
                    date = datetime.datetime.strptime(ch.strip(), "%Y-%m-%dT%H:%M:%S.%fZ")
                    self.out[-1][self.tag] = date
            
            def endElement(self, name):
                pass
        
        p = Popen(['svn', 'log', '--xml', '-v', self.dir], stdout=PIPE, stdin=PIPE, 
                  close_fds=True)
        xml_output = p.communicate()[0].decode('utf-8')
        
        handler = Handler()
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.parse(StringIO(xml_output))
        
        self.log = handler.out
        return self.log
    
    def update(self, r=None):
        args = ['svn', 'update']
        if r: args += ['-r', str(r)]
        args += [self.dir]
        
        p = Popen(args, stdout=PIPE, stdin=PIPE, close_fds=True)
        p.communicate()
    
    def __init__(self, dir, update=True):
        self.log = None
        self.index = -1
        self.dir = dir
        
        if update:
            self.update()
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return self.next()  
    
    def next(self):
        self.index += 1
        if self.index < len(self.get_log()):
            self.update(self.get_log()[self.index]["revision"])
            return self.get_log()[self.index]
        else:
            raise StopIteration


def test(dir):
    x = SVNDirectory(dir)
    l = len(x.get_log())
    print ("First: r%s, last: r%s, count: %s" % (x.get_log()[0]['revision'], x.get_log()[-1]['revision'], l))
    for n, i in enumerate(x):
        print("(%s/%s) r%s: [%s] %s" % (n+1, l, i['revision'], i['author'], i['msg']))
    print("Done!")