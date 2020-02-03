import sys
import pytest
import paramiko


class DibCtlPlugin(object):
    def __init__(self, ssh, tos, environment_variables):
        self.cached_ssh_backend = None
        self.env_vars = environment_variables
        self.tos = tos
        self.ssh_data = ssh
        self.enable_control_master = False  # I wasn't able to make it stable enough, so it's disabled
        try:
            import testinfra
            self.testinfra = testinfra
        except (ImportError,ModuleNotFoundError):
            print("Warning: no testinfra installed, ssh_backend fixture is unavaiable")
            self.testinfra = None
        self.sshclient = paramiko.SSHClient()

    @pytest.fixture
    def flavor(self, request):
        return self.tos.flavor

    def flavor_meta(self, request):
        return self.tos.flavor().get_keys()

    @pytest.fixture
    def ips(self, request):
        return self.tos.ips()

    @pytest.fixture
    def ips_v4(self, request):
        return self.tos.ips_by_version(version=4)

    @pytest.fixture
    def ips_v6(self, request):
        return self.tos.ips_by_version(version=6)

    @pytest.fixture
    def main_ip(self, request):
        return self.tos.ip

    @pytest.fixture
    def network(self, request):
        return self.tos.os_instance.interface_list()

    @pytest.fixture
    def instance(self, request):
        return self.tos.os_instance

    @pytest.fixture
    def ssh(self, request):
        return self.ssh_data.info()

    @pytest.fixture
    def wait_for_port(self, request):
        def wfp(port=None, timeout=None):
            if port is None:
                port = 22  # FIXME From image configuration!!!!
            if timeout is None:
                timeout = 60  # FIXME from image configuration!!!!
            return self.tos.wait_for_port(port, timeout)
        return wfp

    @pytest.fixture
    def ssh_backend(self, request):
        if not self.ssh_data:
            raise ValueError("no ssh settings available in image config")
        if not self.cached_ssh_backend:
            if not self.testinfra:
                raise ImportError(
                    "ssh_backend is unavailable because testinfra module"
                    "is not found."
                )
            self.cached_ssh_backend = self.testinfra.get_backend(
                self.ssh_data.connector(),
                ssh_config=self.ssh_data.config()
                )
        return self.cached_ssh_backend

    @pytest.fixture
    def environment_variables(self, request):
        return self.env_vars

    @pytest.fixture
    def port(self, request):
        raise NotImplementedError
        return {'ip': 0, 'port': 0, 'timeout': 0, 'delay': 0.0}

    @pytest.fixture
    def nova(self, request):
        return self.tos.os.nova

    @pytest.fixture
    def glance(self, request):
        return self.tos.os.glance

    @pytest.fixture
    def image_info(self, request):
        return self.tos.get_image_info()

    @pytest.fixture
    def image_config(self, request):
        return self.tos.image

    @pytest.fixture
    def console_output(self, request):
        return self.tos.os_instance.get_console_output()

    @pytest.fixture
    def ssh_client(self):
        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return self.sshclient


def runner(path, ssh, tos, environment_variables, timeout_val, continue_on_fail):
    cmdline = [path, '-v', '-s']
    dibctl_plugin = DibCtlPlugin(ssh, tos, environment_variables)
    sys.stdout.flush()
    if not continue_on_fail:
        cmdline.append('-x')
    result = pytest.main(cmdline, plugins=[dibctl_plugin])
    sys.stdout.flush()
    if result == 0:
        return True
    else:
        return False
