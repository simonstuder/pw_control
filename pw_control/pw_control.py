
import subprocess as sp
import os
import threading
import time
from typing import Any, Callable
import logging
from pprint import pprint


# TODO:
# - use Nodes

def check_pw_link_installed():
    output: str = exec_shell_cmd("pw-link --version")
    # TODO: check output if not installed
    return True

def exec_shell_cmd(c) -> str:
    p: sp.Popen = sp.Popen(c, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, encoding='utf-8')
    p.wait()
    if p.stdout and p.stderr:
        output: str = p.stdout.read() + p.stderr.read()
    else:
        raise BaseException("no stdout or stderr in exec_shell_cmd")
    return output


class Port:
    def __init__(self,names:list[str], id:str, type:str) -> None:
        self.names: list[str] = names
        self.name: str = names[0]
        self.id: str = id
        self.type: str = type

    def __str__(self) -> str:
        #return (f"Port [{self.id}] ({self.type}) {self.name}\n\t{self.names}")
        return (f"Port [{self.id}] ({self.type}) {self.name}")

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self,o) -> bool:
        if o==None:
            return False
        if not isinstance(o,Port):
            logging.warn(f"wrong type in Port comparison: {o!r}")
            return False
        return self.id==o.id

    def connect(self, other, raiseOnError=True) -> None:
        if not self.type=="o":
            return
        o: str = exec_shell_cmd(f"pw-link {self.name} {other.name}")
        if raiseOnError and "File exists" in o:
            raise Exception("This link exists already")



class Link:
    def __init__(self, id:str, p1:Port, p2:Port) -> None:
        self.id:str = id
        self.ports: list[Port] = [p1, p2]
        #logging.info("link init")
        #logging.info(self.ports)

    def __str__(self) -> str:
        return (f"Link [{self.id}] [{self.ports[0].id}] {self.ports[0].name} -> [{self.ports[1].id}] {self.ports[1].name}")

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self,o) -> bool:
        if o==None:
            return False
        return self.id==o.id and self.ports[0].id==o.ports[0].id and self.ports[1].id==o.ports[1].id

    def disconnect(self, raiseOnError=True):
        o = exec_shell_cmd(f"pw-link -d {self.ports[0].id} {self.ports[1].id}")
        if raiseOnError and "No such file or directory" in o:
            raise Exception("This link does not exists")


class PW_Control:
    def __init__(self,monitorOutput:str="stdout"):
        self.monitorOutputTarget:str = monitorOutput
        self.monitorProcess: sp.Popen[str] = sp.Popen("pw-link -liom", stdout=sp.PIPE, stderr=sp.PIPE, shell=True, encoding='utf-8')
        self.lastInitialMsg:float = -1
        self.ports: dict[str, dict[int,Port]] = {}
        self.links: dict[int,Link] = {}

        def checkMonitor() -> None:
            self.lastInitialMsg = time.time()

            if not self.monitorProcess.stdout:
                return

            for l in self.monitorProcess.stdout:
                l:str = l.strip()
                if l==None:
                    return
                if l==b'':
                    continue
                if l[0] == "=":
                    self.lastInitialMsg = time.time()
                else:
                    # Update in case someone else made changes on the system
                    self.update_info()

                self._monitorOutput(f"[PW_Monitor] {l}")

        self.monitor_t: threading.Thread = threading.Thread(target=checkMonitor,daemon=True,args=())
        self.monitor_t.start()
        self.update_info()

        while time.time()-self.lastInitialMsg<0.100:
            time.sleep(0.1)
        self._monitorOutput("[PW_Control] ready\n")

    def _monitorOutput(self,v) -> None:
        if self.monitorOutputTarget=="stdout":
            logging.info(v)

    def __str__(self) -> str:
        return "== Linker ==\n\n"+self.getAllPortsAsString()+self.getAllLinksAsString()

    def __repr__(self) -> str:
        return str(self)

    def getAllPortsAsString(self) -> str:
        s:str = "= Output Ports =\n"
        for p in self.ports["o"].values():
            s += str(p)+"\n"
        s += "\n= Input Ports =\n"
        for p in self.ports["i"].values():
            s += str(p)+"\n"
        return s

    def getAllLinksAsString(self) -> str:
        s:str = "Links:\n"
        for l in self.links.values():
            s += str(l)+"\n"
        return s

    def update_info(self) -> None:
        self.ports = self.get_ports()
        self.links = self.get_links()

    def get_port(self,v,type="") -> list[Port]:
        if isinstance(v,Port):
            return [v]

        ret: list[Port] = []
        if isinstance(v,int):
            if type in ["o",""]:
                if v in self.ports["o"]:
                    ret.append(self.ports["o"][v])
            if type in ["i",""]:
                if v in self.ports["i"]:
                    ret.append(self.ports["i"][v])

        if isinstance(v,str):
            if type in ["o",""]:
                ps: list[Port] = self.search_ports_for_name(v,"o")
                if len(ps)>0:
                    ret += ps
            if type in ["i",""]:
                ps: list[Port] = self.search_ports_for_name(v,"i")
                if len(ps)>0:
                    ret += ps
        return ret

    def search_ports_for_name(self,n,type="o") -> list[Port]:
        ps: list[Port] = [p for p in self.ports[type].values() if p.name==n]
        if len(ps)>0:
            return ps
        ps: list[Port] = [p for p in self.ports[type].values() if n in p.name]
        return ps

    def get_link(self,v1v,v2v=None) -> list[Link]:

        if isinstance(v1v,int) and v2v==None:
            if v1v in self.links:
                return [self.links[v1v]]
            return []
        if isinstance(v1v,Link):
            return [v1v]

        v1 = self.get_port(v1v,type="o")
        if len(v1)==0:
            return []
        #logging.info(f"v1: {[f'{v.name}({v.id})' for v in v1]}")

        v2 = self.get_port(v2v,type="i")
        if len(v2)==0:
            return []
        #logging.info(f"v2: {[f'{v.name}({v.id})' for v in v2]}")

        return [l for l in self.links.values() if l.ports[0]==v1[0] and l.ports[1]==v2[0]]

    def connect(self,p1v,p2v=None,raiseOnError=True) -> Link|None:
        if isinstance(p1v, tuple):
            p2v = p1v[1]
            p1v = p1v[0]

        p1 = self.get_port(p1v,"o")
        if len(p1)==0:
            if raiseOnError:
                raise Exception(f"{p1v} does not exists or is not specific enough")
            return
        p2 = self.get_port(p2v,"i")
        if len(p2)==0:
            if raiseOnError:
                raise Exception(f"{p2v} does not exists or is not specific enough")
            return

        p1[0].connect(p2[0],raiseOnError)

        self.update_info()

        created_link = self.get_link(p1[0],p2[0])
        if len(created_link)<1:
            raise Exception("created Link not found")

        return created_link[0]

    def disconnect(self,p1,p2=None,raiseOnError=True) -> None:
        ls: list[Link] = self.get_link(p1,p2)
        if len(ls)==0:
            if raiseOnError:
                raise Exception(f"Link {p1} {p2} does not exist")
            return

        logging.info("found links to disconnect")

        for link in ls:
            link.disconnect(raiseOnError)

        self.update_info()



    def get_links(self) -> dict[int,Link]:
        outputs = [l.split() for l in exec_shell_cmd(f"pw-link -Il").strip().split(os.linesep)]

        links: list[list[int]] = []
        for i in range(len(outputs)):
            if len(outputs[i])<1:
                continue
            if outputs[i][1] == '|<-':
                pass
                #links.append([int(outputs[i][0]),int(outputs[i][2]), int(outputs[i-1][0])])
            elif outputs[i][1] == '|->':
                links.append([int(outputs[i][0]),int(outputs[i-1][0]), int(outputs[i][2])])

        links_d: dict[int, Link] = {}
        for l in links:
            p1 = self.get_port(l[1])
            p2 = self.get_port(l[2])
            if len(p1)<1 or len(p2)<1:
                continue
            links_d[l[0]] = Link(str(l[0]), p1[0], p2[0])

        return links_d

    def get_ports(self,which="all") -> dict[str, dict[int,Port]]:
        which2arg: dict[str,str] = {'all': 'oi','i':'i','in':'i','inputs':'i','input':'i','o':'o','out':'o','output':'o','outputs':'o'}
        which = which2arg[which]

        ports:dict[str,dict[int,Port]] = {}
        for v in which:
            outputs = [o.split() for o in exec_shell_cmd(f"pw-link -I{v}v").strip().split(os.linesep)]

            last_port:int = 0
            for i in range(len(outputs)):
                if len(outputs[i])<1:
                    continue
                if outputs[i][0].isnumeric():
                    last_port = i
                else:
                    outputs[last_port] += outputs[i]

            outputs = [o for o in outputs if o[0].isnumeric()]

            out_ports:dict[int,Port] = {}
            for o in outputs:
                out_ports[int(o[0])] = Port(o[1:], int(o[0]), v)

            ports[v] = out_ports

        return ports




    def create_sink(self,name:str="sink_name", channels:int=2, format=None, rate=None, channel_map=None, sink_properties=None, duplicates:str="ignore",waitForExisting:bool=True) -> int:

        if not duplicates=="ignore":
            sinks: dict[str,Any] = self.get_sinks()
            for sn in sinks:
                s: dict = sinks[sn]
                if s["Name"]==name:
                    if duplicates=="Exception":
                        raise Exception(f"Sink with name {name} exists already")
                    else:
                        return -1


        cmd: str = f"pactl load-module module-null-sink sink_name={name} {'channels='+str(channels) if channels!=None else ''} {'format='+format if format!=None else ''} {'rate='+str(rate) if rate!=None else ''} {'channel_map='+channel_map if channel_map!=None else ''} {'sink_properties='+sink_properties if sink_properties!=None else ''}"
        #logging.info("running",cmd)
        p: sp.Popen[str] = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        c: tuple[str,str] = p.communicate()
        if len(c[1])>0:
            logging.error("error")
            logging.error(c[1])
            raise Exception(f"Sink could not be created, {c[1]}")

        id: int = int(c[0].strip())

        if waitForExisting:
            found: bool = False
            while not found:
                sinks: dict[str,Any] = self.get_sinks()
                for sn in sinks:
                    s: dict = sinks[sn]
                    if s["Name"]==name:
                        found = True
                        break
                time.sleep(0.1)

        return id

    def delete_sink(self,name:str="sink_name", waitForRemoved:bool=True, handleNotExisting="ignore"):
        logging.info("delete_sink",name)

        if not isinstance(name,int):
            sinks: dict[str,Any] = self.get_sinks()

            sink: dict|None = None
            for sn in sinks:
                s: dict = sinks[sn]
                if s["Name"]==name:
                    sink = s
                    break

            if sink==None:
                logging.warn("sink not found")
                if handleNotExisting=="ignore":
                    return
                elif handleNotExisting=="stdout":
                    print("sink not found")
                    return
                elif handleNotExisting=="Exception":
                    raise Exception("sink not found")
                return
            id:str = sink["Owner Module"]
        else:
            id:str = name


        cmd:str = f"pactl unload-module {id}"
        #logging.info("running",cmd)
        p:sp.Popen = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        c: tuple[str,str] = p.communicate()

        if len(c[1]):
            logging.error("error")
            logging.error(c[1])

        if waitForRemoved:
            found: bool = True
            while found:
                found = False
                sinks: dict[str,Any] = self.get_sinks()
                for sn in sinks:
                    s: dict = sinks[sn]
                    if s["Name"]==name:
                        found = True
                        break
                time.sleep(0.1)

    def delete_all_sinks(self) -> bool:
        cmd: str = f"pactl unload-module module-null-sink"
        p: sp.Popen = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        return True

    def _parse_pactl_list(self,s) -> dict[str, Any]:
        l: str = s.split("\n\n")

        def parse_Sink(ls) -> dict[str, Any]:
            #logging.info("parse_Sink")

            def parse_part(ls:list[str], rec_d:int = 0) -> tuple[Any,list[str]]:
                #logging.info("parse_part")
                o: dict = {}
                if rec_d>30:
                    logging.warn("recursion max reached")
                    return o,ls

                while len(ls)>0:
                    l: str = ls[0] # first line
                    indent: int = len(l)-len(l.lstrip())

                    # connect wrapped around lines
                    while len(ls)>1:
                        nindent: int = len(ls[1])-len(ls[1].lstrip())
                        if nindent-indent>1:
                            #logging.info("connecting lines")
                            l += " "+ ls[1].lstrip()
                            #logging.debug(l)
                            if len(ls)>2:
                                ls = [ls[0]]+ls[2:]
                            else:
                                ls = [ls[0]]
                        else:
                            break

                    l:str = l.lstrip()
                    if ":" in l:
                        doub:int = l.index(":")
                    elif "=" in l:
                        doub:int = l.index("=")
                    else:
                        return l,ls

                    k:str = l[0:doub]
                    v:str = l[doub+2:]

                    if len(v)>0:
                        #logging.debug("key:",k,"\tv:",v)
                        o[k] = v
                    else:
                        v,ls = parse_part(ls[1:],rec_d+1)
                        #logging.debug("after parse_part")
                        #logging.debug("key:",k,"\tv:")
                        #logging.debug(v)
                        #logging.debug("rest")
                        #logging.debug(ls)
                        o[k] = v
                    
                    if len(ls)>1:
                        nindent:int = len(ls[1])-len(ls[1].lstrip())
                        if nindent<indent:
                            return o,ls

                    ls = ls[1:]

                return o,ls

            o,ls = parse_part(ls)
            return o



        parsers: dict[str,Callable] = {
                "Sink": parse_Sink
                }

        obs: dict[str, dict] = {}
        for s in l:
            # s is the whole output of a Sink in pactl
            #logging.debug(s)

            lines: list[str] = s.split("\n")
            typ: str = lines[0].split(" ")[0] # typ is 'Sink'
            obs[lines[0]] = parsers[typ](lines[1:]) # lines[0] is 'Sink #96'

        return obs

    def get_sinks(self) -> dict[str,Any]:
        cmd: str = "pactl list sinks"
        p = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        c: str = p.communicate()[0]

        obs: dict[str, Any] = self._parse_pactl_list(c)

        #pprint(obs,width=160)
        return obs


