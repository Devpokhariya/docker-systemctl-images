#! /usr/bin/env python3
""" Testcases for docker-systemctl-replacement functionality """

from __future__ import print_function

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "1.5.4147"

## NOTE:
## The testcases 1000...4999 are using a --root=subdir environment
## The testcases 5000...9999 will start a docker container to work.

import subprocess
import os.path
import time
import datetime
import unittest
import shutil
import inspect
import types
import logging
import re
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json
import sys

if sys.version[0] == '3':
    basestring = str
    xrange = range

logg = logging.getLogger("TESTING")
_python = "/usr/bin/python"
_systemctl_py = "files/docker/systemctl.py"
_top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* ' | grep -v -e ' ps ' -e ' grep ' -e 'kworker/'"
_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"

SAVETO = "localhost:5000/systemctl"
IMAGES = "localhost:5000/systemctl/image"
CENTOS = "centos:7.7.1908"
UBUNTU = "ubuntu:14.04"
OPENSUSE = "opensuse/leap:15.0"

DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"
RUNTIME = "/tmp/run-"

def decodes(text):
    if text is None: return None
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try: 
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def sh____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out
def output2(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode
def background(cmd, shell=True):
    BackgroundProcess = collections.namedtuple("BackgroundProcess", ["pid", "run", "log" ])
    log = open(os.devnull, "wb")
    run = subprocess.Popen(cmd, shell=shell, stdout=log, stderr=log)
    pid = run.pid
    logg.info("PID %s = %s", pid, cmd)
    return BackgroundProcess(pid, run, log)



def _lines(lines):
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def lines(text):
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def grep(pattern, lines):
    for line in _lines(lines):
       if re.search(pattern, line.rstrip()):
           yield line.rstrip()
def greps(lines, pattern):
    return list(grep(pattern, lines))

def download(base_url, filename, into):
    if not os.path.isdir(into):
        os.makedirs(into)
    if not os.path.exists(os.path.join(into, filename)):
        sh____("cd {into} && wget {base_url}/{filename}".format(**locals()))
def text_file(filename, content):
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
def shell_file(filename, content):
    text_file(filename, content)
    os.chmod(filename, 0o770)
def copy_file(filename, target):
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename, target):
    copy_file(filename, target)
    os.chmod(target, 0o750)

def get_caller_name():
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code.co_name
def get_caller_caller_name():
    frame = inspect.currentframe().f_back.f_back.f_back
    return frame.f_code.co_name
def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
       path = path[1:]
    return os.path.join(root, path)
def docname(path):
    return os.path.splitext(os.path.basename(path))[0]

class DockerSystemctlReplacementTest(unittest.TestCase):
    def caller_testname(self):
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix = None):
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self):
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 5000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    def makedirs(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)
    def real_folders(self):
        yield "/etc/systemd/system"
        yield "/var/run/systemd/system"
        yield "/usr/lib/systemd/system"
        yield "/lib/systemd/system"
        yield "/etc/init.d"
        yield "/var/run/init.d"
        yield "/var/run"
        yield "/etc/sysconfig"
        yield "/etc/systemd/system/multi-user.target.wants"
        yield "/usr/bin"
    def rm_zzfiles(self, root):
        for folder in self.real_folders():
            for item in glob(os_path(root, folder + "/zz*")):
                logg.info("rm %s", item)
                os.remove(item)
            for item in glob(os_path(root, folder + "/test_*")):
                logg.info("rm %s", item)
                os.remove(item)
    def root(self, testdir, real = None):
        if real: return "/"
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def user(self):
        import getpass
        getpass.getuser()
    def ip_container(self, name):
        values = output("docker inspect "+name)
        values = json.loads(values)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"]    
    def local_system(self):
        distro, version = "", ""
        if os.path.exists("/etc/os-release"):
            # rhel:7.4 # VERSION="7.4 (Maipo)" ID="rhel" VERSION_ID="7.4"
            # centos:7.3  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # centos:7.4  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # centos:7.7.1908  # VERSION="7 (Core)" ID="centos" VERSION_ID="7"
            # opensuse:42.3 # VERSION="42.3" ID=opensuse VERSION_ID="42.3"
            # opensuse/leap:15.0 # VERSION="15.0" ID="opensuse-leap" VERSION_ID="15.0"
            # ubuntu:16.04 # VERSION="16.04.3 LTS (Xenial Xerus)" ID=ubuntu VERSION_ID="16.04"
            # ubuntu:18.04 # VERSION="18.04.1 LTS (Bionic Beaver)" ID=ubuntu VERSION_ID="18.04"
            for line in open("/etc/os-release"):
                key, value = "", ""
                m = re.match('^([_\\w]+)=([^"].*).*', line.strip())
                if m:
                    key, value = m.group(1), m.group(2)
                m = re.match('^([_\\w]+)="([^"]*)".*', line.strip())
                if m:
                    key, value = m.group(1), m.group(2)
                # logg.debug("%s => '%s' '%s'", line.strip(), key, value)
                if key in ["ID"]:
                    distro = value.replace("-","/")
                if key in ["VERSION_ID"]:
                    version = value
        if os.path.exists("/etc/redhat-release"):
            for line in open("/etc/redhat-release"):
                m = re.search("release (\\d+[.]\\d+).*", line)
                if m:
                    distro = "rhel"
                    version = m.group(1)
        if os.path.exists("/etc/centos-release"):
            # CentOS Linux release 7.5.1804 (Core)
            for line in open("/etc/centos-release"):
                m = re.search("release (\\d+[.]\\d+).*", line)
                if m:
                    distro = "centos"
                    version = m.group(1)
        logg.info(":: local_system %s:%s", distro, version)
        if distro and version:
            return "%s:%s" % (distro, version)
        return ""
    def with_local_ubuntu_mirror(self, ver = None):
        """ detects a local ubuntu mirror or starts a local
            docker container with a ubunut repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000/mirror-packages"
        rep = "ubuntu-repo"
        ver = ver or UBUNTU.split(":")[1]
        return self.with_local(rmi, rep, ver, "archive.ubuntu.com", "security.ubuntu.com")
    def with_local_centos_mirror(self, ver = None):
        """ detects a local centos mirror or starts a local
            docker container with a centos repo mirror. It
            will return the setting for extrahosts"""
        rmi = "localhost:5000/mirror-packages"
        rep = "centos-repo"
        ver = ver or CENTOS.split(":")[1]
        return self.with_local(rmi, rep, ver, "mirrorlist.centos.org")
    def with_local_opensuse_mirror(self, ver = None):
        """ detects a local opensuse mirror or starts a local
            docker container with a centos repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000/mirror-packages"
        rep = "opensuse-repo"
        ver = ver or OPENSUSE.split(":")[1]
        return self.with_local(rmi, rep, ver, "download.opensuse.org")
    def with_local(self, rmi, rep, ver, *hosts):
        image = "{rmi}/{rep}:{ver}".format(**locals())
        container = "{rep}-{ver}".format(**locals())
        out, err, ok = output3("docker inspect {image}".format(**locals()))
        image_found = json.loads(out)
        if not image_found:
           return {}
        out, err, ok = output3("docker inspect {container}".format(**locals()))
        container_found = json.loads(out)
        if container_found:
            container_status = container_found[0]["State"]["Status"]
            logg.info("::: %s -> %s", container, container_status)
            latest_image_id = image_found[0]["Id"]
            container_image_id = container_found[0]["Image"]
            if latest_image_id != container_image_id or container_status not in ["running"]:
                cmd = "docker rm --force {container}"
                sx____(cmd.format(**locals()))
                container_found = []
        if not container_found:
            cmd = "docker run --rm=true --detach --name {container} {image}"
            sh____(cmd.format(**locals()))
        ip_a = self.ip_container(container)
        logg.info("::: %s => %s", container, ip_a)
        return dict(zip(hosts, [ ip_a ] * len(hosts)))
    def with_local_mirror(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        hosts = {}
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            hosts = self.with_local_centos_mirror(version)
        if image.startswith("opensuse/leap:"):
            version = image[len("opensuse/leap:"):]
            hosts = self.with_local_opensuse_mirror(version)
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            hosts = self.with_local_opensuse_mirror(version)
        if image.startswith("ubuntu:"):
            version = image[len("ubuntu:"):]
            hosts = self.with_local_ubuntu_mirror(version)
        return hosts
    def add_hosts(self, hosts):
        return " ".join(["--add-host %s:%s" % (host, ip_a) for host, ip_a in hosts.items() ])
        # for host, ip_a in mapping.items():
        #    yield "--add-host {host}:{ip_a}"
    def local_image(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if os.environ.get("NONLOCAL",""):
            return image
        hosts =  self.with_local_mirror(image)
        if hosts:
            add_hosts = self.add_hosts(hosts)
            logg.debug("%s %s", add_hosts, image)
            return "{add_hosts} {image}".format(**locals())
        return image
    def local_addhosts(self, dockerfile):
        image = ""
        for line in open(dockerfile):
            m = re.match('[Ff][Rr][Oo][Mm] *"([^"]*)"', line)
            if m: 
                image = m.group(1)
                break
            m = re.match("[Ff][Rr][Oo][Mm] *(\w[^ ]*)", line)
            if m: 
                image = m.group(1).strip()
                break
        logg.debug("--\n-- '%s' FROM '%s'", dockerfile, image)
        if image:
            hosts = self.with_local_mirror(image)
            return self.add_hosts(hosts)
        return ""
    def drop_container(self, name):
        cmd = "docker rm --force {name}"
        sx____(cmd.format(**locals()))
    def drop_centos(self):
        self.drop_container("centos")
    def drop_ubuntu(self):
        self.drop_container("ubuntu")
    def drop_opensuse(self):
        self.drop_container("opensuse")
    def make_opensuse(self):
        self.make_container("opensuse", OPENSUSE)
    def make_ubuntu(self):
        self.make_container("ubuntu", UBUNTU)
    def make_centos(self):
        self.make_container("centos", CENTOS)
    def make_container(self, name, image):
        self.drop_container(name)
        local_image = self.local_image(image)
        cmd = "docker run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd.format(**locals()))
        print("                 # " + local_image)
        print("  docker exec -it "+name+" bash")
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_100(self):
        logg.info("\n  CENTOS = '%s'", CENTOS)
        self.with_local_centos_mirror()
    def test_101_systemctl_testfile(self):
        """ the systemctl.py file to be tested does exist """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s",  root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(_systemctl_py, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
    def test_102_systemctl_version(self):
        systemctl = _systemctl_py 
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "systemd 219"))
        self.assertTrue(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def real_102_systemctl_version(self):
        cmd = "systemctl --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"systemd [234]\d\d"))
        self.assertFalse(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_103_systemctl_help(self):
        """ the '--help' option and 'help' command do work """
        systemctl = _systemctl_py
        cmd = "{systemctl} --help"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "--root=PATH"))
        self.assertTrue(greps(out, "--verbose"))
        self.assertTrue(greps(out, "--init"))
        self.assertTrue(greps(out, "for more information"))
        self.assertFalse(greps(out, "reload-or-try-restart"))
        cmd = "{systemctl} help" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "--verbose"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
    def test_701_centos_httpd_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        name="centos-httpd"
        dockerfile="centos-httpd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; wget -O {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_705_centos_httpd_not_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode
            THEN it fails."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        name="centos-httpd"
        dockerfile="centos-httpd-not-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname} sleep 300"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "docker exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit httpd.service not for --user mode"))
        cmd = "docker exec {testname} /usr/sbin/httpd -DFOREGROUND"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "could not bind to address 0.0.0.0:80"))
        self.assertTrue(greps(err, "Unable to open logs"))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_706_centos_httpd_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode.
            THEN it succeeds if modified"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        name="centos-httpd"
        dockerfile="centos-httpd-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname} sleep 300"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 0)
        cmd = "docker rm -f {testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; wget -O {testdir}/{testname}.txt http://{container}:8080"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "apache.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_712_centos_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        name="centos-postgres"
        dockerfile="centos-postgres.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = "sleep 5; {login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_715_centos_postgres_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
             AND in this variant it runs under User=postgres right
               there from PID-1 started implicity in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        name="centos-postgres"
        dockerfile="centos-postgres-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        runtime = RUNTIME
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = "sleep 5; {login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} ls {runtime}postgres/run"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:{runtime}postgres/run/postgresql.service.status {testdir}/postgresql.service.status"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "postgres.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_720_ubuntu_apache2(self):
        """ WHEN using a systemd enabled Ubuntu as the base image
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        self.skipTest("test_721 makes it through a dockerfile")
        testname = self.testname()
        testdir = self.testdir()
        saveto = SAVETO
        images = IMAGES
        basename = "ubuntu:16.04"
        savename = "ubuntu-apache2-test"
        image = self.local_image(basename)
        python_base = os.path.basename(_python)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, port, basename)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} apt-get update"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} apt-get install -y apache2 {python_base}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable apache2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        # .........................................
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; wget -O {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_721_ubuntu_apache2(self):
        """ WHEN using a dockerfile for systemd enabled Ubuntu
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile="ubuntu-apache2.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; wget -O {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_730_centos_lamp_stack(self):
        """ Check setup of Linux/Mariadb/Apache/Php on CentOs"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name="centos-lamp-stack"
        dockerfile="centos-lamp-stack.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_740_opensuse_lamp_stack(self):
        """ Check setup of Linux/Mariadb/Apache/Php" on Opensuse"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname=self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name="opensuse-lamp-stack"
        dockerfile="opensuse-lamp-stack.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_741_opensuse_lamp_stack_php7(self):
        """ Check setup of Linux/Mariadb/Apache/Php" on Opensuse later than 15.x"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname=self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name="opensuse-lamp-stack-php7"
        dockerfile="opensuse-lamp-stack-php7.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_750_centos_elasticsearch(self):
        """ Check setup of ElasticSearch on CentOs"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        base_url = "https://download.elastic.co/elasticsearch/elasticsearch"
        filename = "elasticsearch-1.7.3.noarch.rpm"
        into_dir = "Software/ElasticSearch"
        download(base_url, filename, into_dir)
        self.assertTrue(greps(os.listdir("Software/ElasticSearch"), filename))
        #
        testname=self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        port=self.testport()
        name="centos-elasticsearch"
        dockerfile="centos-elasticsearch.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "docker exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        cmd = "sleep 8; wget -O {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        # CHECK
        cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        systemctl_log = open(testdir+"/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_762_centos_tomcat_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an tomcat service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        dockerfile="centos-tomcat.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; wget -O {testdir}/{testname}.txt http://{container}:8080/sample"
        sh____(cmd.format(**locals()))
        cmd = "grep Hello {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_765_centos_tomcat_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an tomcat service 
                 being installed and enabled.
            In this case the container is run in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        dockerfile="centos-tomcat-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; wget -O {testdir}/{testname}.txt http://{container}:8080/sample"
        sh____(cmd.format(**locals()))
        cmd = "grep Hello {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "tomcat.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_772_centos_cntlm_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an cntlm service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        dockerfile="centos-cntlm.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; docker exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "http_proxy={container}:3128 wget -O {testdir}/{testname}.txt http://www.google.com --timeout=4"
        # cmd = "sleep 5; http_proxy=127.0.0.1:3128 wget -O {testdir}/{testname}.txt http://www.google.com --timeout=4"
        sh____(cmd.format(**locals()))
        cmd = "grep '<img alt=.Google.' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_775_centos_cntlm_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an cntlm service 
                 being installed and enabled.
            In this case the container is run in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        dockerfile="centos-cntlm-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; docker exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "http_proxy={container}:3128 wget -O {testdir}/{testname}.txt http://www.google.com --timeout=4"
        # cmd = "http_proxy=127.0.0.1:3128 wget -O {testdir}/{testname}.txt http://www.google.com --timeout=4"
        sh____(cmd.format(**locals()))
        cmd = "grep '<img alt=.Google.' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_778_centos_ssh_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        dockerfile="centos-sshd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2; docker exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        allows="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p Test.P@ssw0rd scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        #cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        #sh____(cmd.format(**locals()))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
        logg.warning("centos-sshd is incomplete without .socket support in systemctl.py")
        logg.warning("the scp call will succeed only once - the sshd is dead after that")

    def test_850_centos_elasticsearch_setup(self):
        """ Check setup of ElasticSearch on CentOs"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir()
        setupfile="centos-elasticsearch-setup.yml"
        savename = docname(setupfile)
        basename = CENTOS
        saveto = SAVETO
        images = IMAGES
        image = self.local_image(basename)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {image} sleep infinity"
        sh____(cmd.format(**locals()))
        prepare = " --limit {testname} -e ansible_user=root"
        cmd = "ansible-playbook -i centos-elasticsearch-setup.ini ansible-sudo.yml -vv" + prepare
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} grep __version__ /usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "ansible-playbook -i centos-elasticsearch-setup.ini centos-elasticsearch-setup.yml -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} grep __version__ /usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker commit -c 'CMD /usr/bin/systemctl' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "docker exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        cmd = "sleep 9; wget -O {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir+"/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "docker tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_900_ansible_test(self):
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        sh____("ansible-playbook --version | grep ansible-playbook.2") # atleast version2
        new_image1 = "localhost:5000/systemctl:serversystem"
        new_image2 = "localhost:5000/systemctl:virtualdesktop"
        rmi_commit1 = 'docker rmi "{new_image1}"'
        rmi_commit2 = 'docker rmi "{new_image2}"'
        sx____(rmi_commit1.format(**locals()))
        sx____(rmi_commit2.format(**locals()))
        if False:
            self.test_901_ansible_download_software()
            self.test_902_ansible_restart_docker_build_compose()
            self.test_903_ansible_run_build_step_playbooks()
            self.test_904_ansible_save_build_step_as_new_images()
            self.test_905_ansible_restart_docker_start_compose()
            self.test_906_ansible_unlock_jenkins()
            self.test_907_ansible_check_jenkins_login()
            self.test_908_commit_containers_as_images()
            self.test_909_ansible_stop_all_containers()
    def test_901_ansible_download_software(self):
        """ download the software parts (will be done just once) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        sh____("ansible-playbook download-jenkins.yml -vv")
        sh____("ansible-playbook download-selenium.yml -vv")
        sh____("ansible-playbook download-firefox.yml -vv")
        # CHECK
        self.assertTrue(greps(os.listdir("Software/Jenkins"), "^jenkins.*[.]rpm"))
        self.assertTrue(greps(os.listdir("Software/Selenium"), "^selenium-.*[.]tar.gz"))
        self.assertTrue(greps(os.listdir("Software/Selenium"), "^selenium-server.*[.]jar"))
        self.assertTrue(greps(os.listdir("Software/CentOS"), "^firefox.*[.]centos[.]x86_64[.]rpm"))
    def test_902_ansible_restart_docker_build_compose(self):
        """ bring up the build-step deployment containers """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        compose_and_repo = "docker-build-compose"
        if self.local_image(CENTOS):
           compose_and_repo += "-with-repo"
        drop_old_containers = "docker-compose -p systemctl1 -f {compose_and_repo}.yml down".format(**locals())
        make_new_containers = "docker-compose -p systemctl1 -f {compose_and_repo}.yml up -d".format(**locals())
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
        # CHECK
        self.assertTrue(greps(output("docker ps"), " systemctl1_virtualdesktop_1$"))
        self.assertTrue(greps(output("docker ps"), " systemctl1_serversystem_1$"))
    def test_903_ansible_run_build_step_playbooks(self):
        """ run the build-playbook (using ansible roles) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testdir = self.testdir()
        # WHEN environment is prepared
        make_logfile_1 = "docker exec systemctl1_serversystem_1 bash -c 'touch /var/log/systemctl.log'"
        make_logfile_2 = "docker exec systemctl1_virtualdesktop_1 bash -c 'touch /var/log/systemctl.log'"
        chmod_logfile_1 = "docker exec systemctl1_serversystem_1 bash -c 'chmod 666 /var/log/systemctl.log'"
        chmod_logfile_2 = "docker exec systemctl1_virtualdesktop_1 bash -c 'chmod 666 /var/log/systemctl.log'"
        sh____(make_logfile_1)
        sh____(make_logfile_2)
        sh____(chmod_logfile_1)
        sh____(chmod_logfile_2)
        # THEN ready to run the deployment playbook
        prep = "ansible-sudo.yml"
        playbooks = "docker-build-systems.yml"
        inventory = "docker-build-compose.ini"
        variables = "-e LOCAL=yes -e jenkins_prefix=/buildserver"
        cmd = "ansible-playbook -i {inventory} {prep} -vv"
        sh____(cmd.format(**locals()))
        cmd = "ansible-playbook -i {inventory} {variables} {playbooks} -vv"
        sh____(cmd.format(**locals()))
        #
        # CHECK
        read_logfile_1 = "docker cp systemctl1_serversystem_1:/var/log/systemctl.log {testdir}/systemctl.server.log"
        read_logfile_2 = "docker cp systemctl1_virtualdesktop_1:/var/log/systemctl.log {testdir}/systemctl.desktop.log"
        sh____(read_logfile_1.format(**locals()))
        sh____(read_logfile_2.format(**locals()))
        systemctl_server_log = open(testdir+"/systemctl.server.log").read()
        systemctl_desktop_log = open(testdir+"/systemctl.desktop.log").read()
        self.assertFalse(greps(systemctl_server_log, " ERROR "))
        self.assertFalse(greps(systemctl_desktop_log, " ERROR "))
        self.assertGreater(len(greps(systemctl_server_log, " INFO ")), 6)
        self.assertGreater(len(greps(systemctl_desktop_log, " INFO ")), 6)
        self.assertTrue(greps(systemctl_server_log, "/systemctl daemon-reload"))
        # self.assertTrue(greps(systemctl_server_log, "/systemctl status jenkins.service"))
        # self.assertTrue(greps(systemctl_server.log, "--property=ActiveState")) # <<< new
        self.assertTrue(greps(systemctl_server_log, "/systemctl show jenkins"))
        self.assertTrue(greps(systemctl_desktop_log, "/systemctl show xvnc.service"))
        self.assertTrue(greps(systemctl_desktop_log, "/systemctl enable xvnc.service"))
        self.assertTrue(greps(systemctl_desktop_log, "/systemctl enable selenium.service"))
        self.assertTrue(greps(systemctl_desktop_log, "/systemctl is-enabled selenium.service"))
        self.assertTrue(greps(systemctl_desktop_log, "/systemctl daemon-reload"))
        self.rm_testdir()
    def test_904_ansible_save_build_step_as_new_images(self):
        # stop the containers but keep them around
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        inventory = "docker-build-compose.ini"
        playbooks = "docker-build-stop.yml"
        variables = "-e LOCAL=yes"
        cmd = "docker exec systemctl1_virtualdesktop_1 bash -c 'systemctl status jenkins'"
        sx____(cmd.format(**locals()))
        cmd = "ansible-playbook -i {inventory} {variables} {playbooks} -vv"
        sh____(cmd.format(**locals()))
        message = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        startup = "CMD '/usr/bin/systemctl'"
        container1 = "systemctl1_serversystem_1"
        new_image1 = "localhost:5000/systemctl/serversystem"
        container2 = "systemctl1_virtualdesktop_1"
        new_image2 = "localhost:5000/systemctl/virtualdesktop"
        commit1 = 'docker commit -c "{startup}" -m "{message}" {container1} "{new_image1}"'
        commit2 = 'docker commit -c "{startup}" -m "{message}" {container2} "{new_image2}"'
        sh____(commit1.format(**locals()))
        sh____(commit2.format(**locals()))
        # CHECK
        self.assertTrue(greps(output("docker images"), SAVETO+".*/serversystem"))
        self.assertTrue(greps(output("docker images"), SAVETO+".*/virtualdesktop"))
    def test_905_ansible_restart_docker_start_compose(self):
        """ bring up the start-step runtime containers from the new images"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        compose_and_repo = "docker-build-compose"
        if self.local_image(CENTOS):
           compose_and_repo += "-with-repo"
        drop_old_build_step = "docker-compose -p systemctl1 -f {compose_and_repo}.yml down".format(**locals())
        drop_old_containers = "docker-compose -p systemctl2 -f docker-start-compose.yml down"
        make_new_containers = "docker-compose -p systemctl2 -f docker-start-compose.yml up -d"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
        time.sleep(2) # sometimes the container dies early
        # CHECK
        self.assertFalse(greps(output("docker ps"), " systemctl1_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " systemctl1_serversystem_1$"))
        self.assertTrue(greps(output("docker ps"), " systemctl2_virtualdesktop_1$"))
        self.assertTrue(greps(output("docker ps"), " systemctl2_serversystem_1$"))
    def test_906_ansible_unlock_jenkins(self):
        """ unlock jenkins as a post-build config-example using selenium-server """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        inventory = "docker-start-compose.ini"
        playbooks = "docker-start-systems.yml"
        variables = "-e LOCAL=yes -e j_username=installs -e j_password=installs.11"
        vartarget = "-e j_url=http://serversystem:8080/buildserver"
        ansible = "ansible-playbook -i {inventory} {variables} {vartarget} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        # CHECK
        test_screenshot = "ls -l *.png"
        sh____(test_screenshot)
    def test_907_ansible_check_jenkins_login(self):
        """ check jenkins runs unlocked as a testcase result """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testdir = self.testdir()
        webtarget = "http://localhost:8080/buildserver/manage"
        weblogin = "--user installs --password installs.11 --auth-no-challenge"
        read_jenkins_html = "wget {weblogin} -O {testdir}/page.html {webtarget}"
        grep_jenkins_html = "grep 'Manage Nodes' {testdir}/page.html"
        sh____(read_jenkins_html.format(**locals()))
        sh____(grep_jenkins_html.format(**locals()))
        self.rm_testdir()
    def test_908_commit_containers_as_images(self):
        saveto = SAVETO
        images = IMAGES
        saveimage = "centos-jenkins"
        new_image1 = "localhost:5000/systemctl/serversystem"
        new_image2 = "localhost:5000/systemctl/virtualdesktop"
        container1 = "systemctl2_serversystem_1"
        container2 = "systemctl2_virtualdesktop_1"
        cmd = 'docker rmi "{saveimage}"'
        sx____(cmd.format(**locals()))
        CMD = 'CMD ["/usr/bin/systemctl"]'
        cmd = "docker commit -c '{CMD}' {container1} {saveto}/{saveimage}:latest"
        sh____(cmd.format(**locals()))
    def test_909_ansible_stop_all_containers(self):
        """ bring up the start-step runtime containers from the new images"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        time.sleep(3)
        drop_old_build_step = "docker-compose -p systemctl1 -f docker-build-compose.yml down"
        drop_old_start_step = "docker-compose -p systemctl2 -f docker-start-compose.yml down"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_start_step}".format(**locals()))
        # CHECK
        self.assertFalse(greps(output("docker ps"), " systemctl1_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " systemctl1_serversystem_1$"))
        self.assertFalse(greps(output("docker ps"), " systemctl2_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " systemctl2_serversystem_1$"))

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
       epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v","--verbose", action="count", default=0,
       help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
       help="systemctl.py file to be tested (%default)")
    _o.add_option("-p","--python", metavar="EXE", default=_python,
       help="use another python execution engine [%default]")
    _o.add_option("-l","--logfile", metavar="FILE", default="",
       help="additionally save the output log to a file [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
       help="capture results as a junit xml file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
           os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
           os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    #
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = [ "test_*" ]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if arg.startswith("_"): arg = arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    if not logfile:
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
            Runner(xmlresults).run(suite)
        else:
            Runner = unittest.TextTestRunner
            Runner(verbosity=opt.verbose).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
        Runner(logfile.stream, verbosity=opt.verbose).run(suite)
