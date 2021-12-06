import subprocess
import sys
import os

currentdir = os.path.dirname(os.path.realpath(__file__))
parentDirectory = os.path.dirname(currentdir)
sys.path.append(os.path.abspath(parentDirectory))

from helpers.common import main

class sshClient(object):

    def __init__(self, **kwargs) -> any:
        if kwargs is None:
            kwargs = {}
        kwargs.setdefault('shell', False)
        kwargs.setdefault('backgroundExecution', False)
        kwargs.setdefault('PubkeyAuthentication', False)
        kwargs.setdefault('sshKeyFile', '~/.ssh/known_hosts')
        kwargs.setdefault('universal_newlines', True)
        kwargs.setdefault('timeout', 15)
        self.shell = kwargs.get('shell')
        self.sshKeyFile = kwargs.get('sshKeyFile')
        self.timeout = kwargs.get('timeout')
        self.PubkeyAuthentication = kwargs.get('PubkeyAuthentication')
        self.backgroundExecution = kwargs.get('backgroundExecution')
        self.universal_newlines = kwargs.get('universal_newlines')
        self.markers ={'start': '~START~', 'end': '~END~'}
        self.cmdArgs = [ 'ssh','-q', '-t', '-T']
        if self.backgroundExecution:
            self.cmdArgs.append('-f')
        if self.PubkeyAuthentication and os.path.isfile(os.path.expanduser(self.sshKeyFile)):
            self.cmdArgs.append('-i')
            self.cmdArgs.append(os.path.expanduser(self.sshKeyFile))
        else:
            pwdAuthOptions = ['StrictHostKeyChecking=no', 'UserKnownHostsFile=/dev/null', 'PubkeyAuthentication=no', 'NumberOfPasswordPrompts=1']
            for sshOption in pwdAuthOptions:
                self.cmdArgs.append('-o')
                self.cmdArgs.append(sshOption)
        self.stdin = subprocess.PIPE
        self.stdout = subprocess.PIPE
        self.closeFileDescriptors = True
        self.port = '22'
        self.username = 'root'
        self.host = 'localhost'
        self.bufsize = 0
        self.session = None
        self.Results = []
        self.commands   = []

    def getCompiler(ext:str = None)->str:
        ext= str(ext).strip() if ext and isinstance(ext,str) else None
        switcher = {
            'py':'python',
            'sh':'sh',
            'pl':'perl'
        }
        return switcher.get(ext.lower(), 'python')

    def connect(self, **kwargs)->any:
        kwargs.setdefault('host', None)
        kwargs.setdefault('user', None)
        kwargs.setdefault('port', None)
        self.host = (kwargs.get('host')).strip() if kwargs.get('host') else self.host
        self.username = (kwargs.get('user')).strip() if kwargs.get('user') else self.username
        self.port = str(kwargs.get('port')) if kwargs.get('port') and isinstance(kwargs.get('port'), int) else self.port
        self.cmdArgs.append('-o')
        self.cmdArgs.append('LogLevel=error')
        self.cmdArgs.append('-p')
        self.cmdArgs.append(self.port)
        self.cmdArgs.append('%s@%s' % (self.username, self.host))
        self.session = subprocess.Popen(self.cmdArgs,
                shell              = self.shell,
                stdin              = self.stdin,
                stdout             = self.stdout,
                universal_newlines = self.universal_newlines,
                bufsize            = self.bufsize,
                close_fds          = self.closeFileDescriptors
            )
        return self.session

    def execute(self, scripts):
        self.commands.append('echo ' + self.markers.get('start'))
        if isinstance(scripts, str):
            self.commands.append(scripts)
        if isinstance(scripts, list):
            for line in scripts:
                self.commands.append(line)
        try:
            if self.session:
                self.commands.append('echo ' + self.markers.get('end'))
                (stdoutdata, stderrdata)  = self.session.communicate('; '.join(self.commands), timeout=self.timeout)
                if not(self.session.poll() == 0):
                    raise subprocess.CalledProcessError(cmd='; '.join(self.commands),returncode=self.session.poll(),output=stderrdata)
                else:
                    start = stdoutdata.find(self.markers.get('start')) + len(self.markers.get('start'))
                    end = stdoutdata.find(self.markers.get('end'))
                    stdoutdata = (stdoutdata[start:end]).strip().replace(os.linesep, '\n')
                    for line in stdoutdata.split('\n'):
                        self.Results.append(line)
                self.session.terminate()
            return self.Results
        except subprocess.CalledProcessError as ex: # error code <> 0
            print ('-------- ERROR ------')
            print(ex.cmd)
            print(ex.returncode)
            print(ex.output)

    def getResults(self, render: bool=True):
        if self.Results:
            if not(render):
                return self.Results
            import pprint
            printer = pprint.PrettyPrinter(indent=4)
            printer.pprint(self.Results)
if __name__ == '__main__':
    sshChannel = sshClient()
    sshChannel.connect(host ='192.168.2.77', user = 'ubuntu', port= 22)
    sshChannel.execute(['id', 'who', 'pwd', 'hostname'])
    sshChannel.getResults()
    sys.exit(main(__file__))


# import re as regex

# s = 'asdf=5;iwantthis123jasd'
# result = regex.match('asdf=5;(.*)123jasd', s)
#ssh-copy-id -i ~/.ssh/id_rsa.pub '192.168.2.77'
