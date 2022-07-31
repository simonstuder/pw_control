
import subprocess as sp
import os
import threading
import time


# TODO:
# - use Nodes

def check_pw_link_installed():
    output = exec_shell_cmd("pw-link --version")
    # TODO: check output if not installed
    return True

def exec_shell_cmd(c):
    p = sp.Popen(c, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, encoding='utf-8')
    p.wait()
    output = p.stdout.read() + p.stderr.read()
    return output


class Port:
    def __init__(self,names,id, type):
        self.names = names
        self.name = names[0]
        self.id = id
        self.type = type

    def __str__(self):
        return (f"Port [{self.id}] ({self.type}) {self.name}\n\t{self.names}")

    def __repr(self):
        return self.__str__(self)

    def __eq__(self,o):
        if o==None:
            return False
        return self.id==o.id

    def connect(self, other, raiseOnError=True):
        if not self.type=="o":
            return
        o = exec_shell_cmd(f"pw-link {self.name} {other.name}")
        if raiseOnError and "File exists" in o:
            raise Exception("This link exists already")



class Link:
    def __init__(self, id, p1, p2):
        self.id = id
        self.ports = [p1, p2]

    def __str__(self):
        return (f"Link [{self.id}] [{self.ports[0].id}] {self.ports[0].name} -> [{self.ports[1].id}] {self.ports[1].name}")

    def __repr(self):
        return self.__str__(self)

    def __eq__(self,o):
        if o==None:
            return False
        return self.id==o.id and self.ports[0].id==o.ports[0].id and self.ports[1].id==o.ports[1].id

    def disconnect(self, raiseOnError=True):
        o = exec_shell_cmd(f"pw-link -d {self.ports[0].id} {self.ports[1].id}")
        if raiseOnError and "No such file or directory" in o:
            raise Exception("This link does not exists")


class PW_Control:
    def __init__(self,monitorOutput="stdout"):
        self.monitorOutputTarget = monitorOutput
        self.monitorProcess = sp.Popen("pw-link -liom", stdout=sp.PIPE, stderr=sp.PIPE, shell=True, encoding='utf-8')

        def checkMonitor(p):
            self.lastInitialMsg = time.time()

            for l in self.monitorProcess.stdout:
                l = l.strip()
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

        self.monitor_t = threading.Thread(target=checkMonitor,daemon=True,args=(self.monitorProcess,))
        self.monitor_t.start()
        self.update_info()

        while time.time()-self.lastInitialMsg<0.100:
            time.sleep(0.1)
        self._monitorOutput("[PW_Control] ready\n")

    def _monitorOutput(self,v):
        if self.monitorOutputTarget=="stdout":
            print(v)

    def __str__(self):
        s = "== Linker ==\n\n"+self.getAllPortsAsString()+self.getAllLinksAsString()
        return s

    def __repr__(self):
        return self.__str__()

    def getAllPortsAsString(self):
        s = "= Output Ports =\n"
        for p in self.ports["o"].values():
            s += str(p)+"\n"
        s += "\n= Input Ports =\n"
        for p in self.ports["i"].values():
            s += str(p)+"\n"
        return s

    def getAllLinksAsString(self):
        s = "Links:\n"
        for l in self.links.values():
            s += str(l)+"\n"
        return s

    def update_info(self):
        self.ports = self.get_ports()
        self.links = self.get_links()

    def get_port(self,v,type="",return_multiple=False):
        if isinstance(v,Port):
            return v
        if isinstance(v,int):
            if type in ["o",""]:
                if v in self.ports["o"]:
                    return self.ports["o"][v]
            if type in ["i",""]:
                if v in self.ports["i"]:
                    return self.ports["i"][v]
            return None

        if isinstance(v,str):
            if type in ["o",""]:
                ps = self.search_ports_for_name(v,"o")
                if len(ps)>0:
                    if return_multiple and len(ps)>1:
                        return ps
                    return ps[0]
            if type in ["i",""]:
                ps = self.search_ports_for_name(v,"i")
                if len(ps)>0:
                    if return_multiple and len(ps)>1:
                        return ps
                    return ps[0]
            return None

    def search_ports_for_name(self,n,type="o"):
        ps = [p for p in self.ports[type].values() if p.name==n]
        if len(ps)>0:
            return ps
        ps = [p for p in self.ports[type].values() if n in p.name]
        return ps

    def get_link(self,v1v,v2v=None,return_multiple=False):

        if isinstance(v1v,int) and v2v==None:
            if v1v in self.links:
                return self.links[v1v]
            return None
        if isinstance(v1v,Link):
            return v1v

        v1 = self.get_port(v1v,type="o",return_multiple=True)
        if v1==None:
            return None
        if isinstance(v1,Port):
            v1 = [v1]
        #print([v.name for v in v1])

        v2 = self.get_port(v2v,type="i",return_multiple=True)
        if v2==None:
            return None
        if isinstance(v2,Port):
            v2 = [v2]
        #print([v.name for v in v2])

        res = [l for l in self.links.values() if l.ports[0] in v1 and l.ports[1] in v2]
        if len(res)>0:
            if return_multiple and len(res)>1:
                return res
            return res[0]

        return None

    def connect(self,p1v,p2v=None,raiseOnError=True):
        if isinstance(p1v, tuple):
            p2v = p1v[1]
            p1v = p1v[0]

        p1 = self.get_port(p1v,"o")
        if raiseOnError and p1==None:
            raise Exception(f"{p1v} does not exists or is not specific enough")
        p2 = self.get_port(p2v,"i")
        if raiseOnError and p2==None:
            raise Exception(f"{p2v} does not exists or is not specific enough")

        p1.connect(p2,raiseOnError)

        self.update_info()

        return self.get_link(p1,p2)

    def disconnect(self,p1,p2=None,raiseOnError=True):
        l = self.get_link(p1,p2)
        if l==None:
            if raiseOnError:
                raise Exception(f"Link {p1} {p2} does not exist")
            return

        l.disconnect(raiseOnError)

        self.update_info()



    def get_links(self):
        outputs = [l.split() for l in exec_shell_cmd(f"pw-link -Il").strip().split(os.linesep)]

        links = []
        for i in range(len(outputs)):
            if len(outputs[i])<1:
                continue
            if outputs[i][1] == '|<-':
                pass
                #links.append([int(outputs[i][0]),int(outputs[i][2]), int(outputs[i-1][0])])
            elif outputs[i][1] == '|->':
                links.append([int(outputs[i][0]),int(outputs[i-1][0]), int(outputs[i][2])])

        links_d = {}
        for l in links:
            links_d[l[0]] = Link(l[0], self.get_port(l[1]), self.get_port(l[2]))

        return links_d

    def get_ports(self,which="all"):
        which2arg = {'all': 'oi','i':'i','in':'i','inputs':'i','input':'i','o':'o','out':'o','output':'o','outputs':'o'}
        which = which2arg[which]

        ports = {}
        for v in which:
            outputs = [o.split() for o in exec_shell_cmd(f"pw-link -I{v}v").strip().split(os.linesep)]

            last_port = 0
            for i in range(len(outputs)):
                if len(outputs[i])<1:
                    continue
                if outputs[i][0].isnumeric():
                    last_port = i
                else:
                    outputs[last_port] += outputs[i]

            outputs = [o for o in outputs if o[0].isnumeric()]

            out_ports = {}
            for o in outputs:
                out_ports[int(o[0])] = Port(o[1:], int(o[0]), v)

            ports[v] = out_ports

        return ports




    def create_sink(self,name="sink_name", channels=2, format=None, rate=None, channel_map=None, sink_properties=None, duplicates="ignore",waitForExisting=True):
        if not duplicates=="ignore":
            sinks = self.get_sinks()
            for sn in sinks:
                s = sinks[sn]
                if s["Name"]==name:
                    if duplicates=="Exception":
                        raise Exception(f"Sink with name {name} exists already")
                    else:
                        return -1


        cmd = f"pactl load-module module-null-sink sink_name={name} {'channels='+str(channels) if channels!=None else ''} {'format='+format if format!=None else ''} {'rate='+str(rate) if rate!=None else ''} {'channel_map='+channel_map if channel_map!=None else ''} {'sink_properties='+sink_properties if sink_properties!=None else ''}"
        #print("running",cmd)
        p = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        c = p.communicate()
        if len(c[1])>0:
            print("error")
            print(c[1])
            return

        id = int(c[0].strip())

        if waitForExisting:
            found = False
            while not found:
                sinks = self.get_sinks()
                for sn in sinks:
                    s = sinks[sn]
                    if s["Name"]==name:
                        found = True
                        break
                time.sleep(0.1)

        return id

    def delete_sink(self,name="sink_name", waitForRemoved=True, handleNotExisting="ignore"):
        print("delete_sink",name)

        if not isinstance(name,int):
            sinks = self.get_sinks()

            sink = None
            for sn in sinks:
                s = sinks[sn]
                if s["Name"]==name:
                    sink = s
                    break

            if sink==None:
                if handleNotExisting=="ignore":
                    return
                elif handleNotExisting=="stdout":
                    print("sink not found")
                    return
                elif handleNotExisting=="Exception":
                    raise Exception("sink not found")
                return
            id = sink["Owner Module"]
        else:
            id = name


        cmd = f"pactl unload-module {id}"
        #print("running",cmd)
        p = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        c = p.communicate()

        if len(c[1]):
            print("error")
            print(c[1])

        if waitForRemoved:
            found = True
            while found:
                found = False
                sinks = self.get_sinks()
                for sn in sinks:
                    s = sinks[sn]
                    if s["Name"]==name:
                        found = True
                        break
                time.sleep(0.1)

    def delete_all_sinks(self,):
        cmd = f"pactl unload-module module-null-sink"
        p = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()

    def _parse_pactl_list(self,s):
        l = s.split("\n\n")

        def parse_Sink(ls):
            #print("parse_Sink")

            def parse_part(ls,rec_d = 0):
                #print("parse_part")
                o = {}
                if rec_d>30:
                    print("recursion max reached")
                    return o,ls

                while len(ls)>0:
                    l = ls[0]
                    indent = len(l)-len(l.lstrip())

                    # connect wrapped around lines
                    while len(ls)>1:
                        nindent = len(ls[1])-len(ls[1].lstrip())
                        if nindent-indent>1:
                            #print("connecting lines")
                            l += " "+ ls[1].lstrip()
                            #print(l)
                            if len(ls)>2:
                                ls = [ls[0]]+ls[2:]
                            else:
                                ls = [ls[0]]
                        else:
                            break

                    l = l.lstrip()
                    if ":" in l:
                        doub = l.index(":")
                    elif "=" in l:
                        doub = l.index("=")
                    else:
                        return l,ls
                    k = l[0:doub]
                    v = l[doub+2:]

                    if len(v)>0:
                        #print("key:",k,"\tv:",v)
                        o[k] = v
                    else:
                        v,ls = parse_part(ls[1:],rec_d+1)
                        #print("after parse_part")
                        #print("key:",k,"\tv:")
                        #pprint(v)
                        #print("rest")
                        #print(ls)
                        o[k] = v
                    
                    if len(ls)>1:
                        nindent = len(ls[1])-len(ls[1].lstrip())
                        if nindent<indent:
                            return o,ls

                    ls = ls[1:]

                return o,ls

            o,ls = parse_part(ls)
            return o



        parsers = {
                "Sink": parse_Sink
                }

        obs = {}
        for s in l:
            #print(s)

            lines = s.split("\n")
            typ = lines[0].split(" ")[0]
            obs[lines[0]] = parsers[typ](lines[1:])

        return obs

    def get_sinks(self,):
        cmd = "pactl list sinks"
        p = sp.Popen(cmd, shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        c = p.communicate()[0]

        obs = self._parse_pactl_list(c)

        #pprint(obs,width=160)
        return obs


