#!/usr/bin/env python3

import os
import subprocess

packages = [
    "curl",
    "default-jdk",
]

SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
TOMCAT_DIR = os.path.join('/opt', 'tomcat')
TOMCAT_SERVICE_PATH = os.path.join('/etc', 'systemd', 'system', 'tomcat.service')

def install_packages(packages):
    run("apt install -y "+ ' '.join(packages))

def prepare_tomcat_user():
    run("groupadd tomcat")
    run("useradd -s /bin/false -g tomcat -d /opt/tomcat tomcat")

def run(command, pipeoutput=False):
    params = {}
    command = command.split(' ')
    if pipeoutput:
        params["stdout"] = params["stderr"] = subprocess.PIPE
    return subprocess.run(command, **params)

def download_tomcat():
    tomcat_dir = '/opt/tomcat'
    if os.path.isdir(tomcat_dir):
        print("the tomcat dir exits, do you wan override it?")
        value = input()
        if value not in ['y', 'Y', 's', 'si', 'yes']:
            print('canceling tomcat instalation')
            return False
        run("rm -R {}".format(tomcat_dir))
        os.mkdir(tomcat_dir)
    else:
        os.mkdir(tomcat_dir)

    tomcat_tar = "https://www-us.apache.org/dist/tomcat/tomcat-9/v9.0.22/bin/apache-tomcat-9.0.22.tar.gz"
    os.chdir('/tmp')
    run("curl -O {}".format(tomcat_tar))
    tar_file = os.path.basename(tomcat_tar)
    run("tar xzvf {} -C {} --strip-components=1".format(tar_file, tomcat_dir))
    run("chgrp -R tomcat {}".format(tomcat_dir))
    os.chdir(tomcat_dir)
    run("chmod -R g+r conf")
    run("chmod g+x conf")
    result = run("chown -R tomcat webapps/ work/ temp/ logs/")
    return result.returncode == 0

def setup_tomcat_service():
    result = run("update-java-alternatives -l", pipeoutput=True)
    if result.returncode != 1:
        print("Unable to get the java alternatives :(")
        return False
    java_alternative = result.stdout.decode().strip("\n\040").split(' ').pop()
    if not os.path.exists(java_alternative):
        print("mmm the java alternative {} doesn't exist".format(java_alternative))
        return False
    template = os.path.join(SCRIPT_DIR, 'tomcat.service')
    content = None
    with open(template) as template_file:
        content = template_file.read()

    content = content.format(java_home=java_alternative)
    with open(TOMCAT_SERVICE_PATH, 'w') as tomcat_service_file:
        tomcat_service_file.write(content)
    return True


install_packages(packages)
prepare_tomcat_user()
downloaded = download_tomcat()
if not downloaded:
    print("The tomcat can't be downloaded :/")

if not os.path.exists(os.path.join(TOMCAT_DIR, 'bin')):
    print("The tomcat bin path doesn't exists unable to continue")
    exit()


if not os.path.isfile(TOMCAT_SERVICE_PATH):
    print("the tomcat service file can't be found trying to install...")
    success = setup_tomcat_service()
    if success:
        print("done bro")
    else:
        print("I fail. do it for your self")

if os.path.isfile(TOMCAT_SERVICE_PATH):
    print("the tomcat service it's installed")
    run("systemctl daemon-reload")
    run("systemctl start tomcat")
    run("systemctl status tomcat")




