import argparse
import json
import os
import sys
import time

import zap_scan

import docker
from docker.errors import ImageNotFound, DockerException, NotFound


class ZAP:
    """
    ZAP class make it possible to run ZAP proxy on specific target
    """

    def __init__(self, target, output_filepath):
        """
        ZAP constructor
        """
        self.results = {}
        self.target = target
        self.output_filepath = output_filepath
        self.zap_image_name = 'owasp/zap2docker-stable'
        self.zap_container_name = 'zap'

        try:
            self.client = docker.from_env()
        except DockerException:
            print(f'[-] Cannot find api. maybe docker is not running.')
            sys.exit(-1)

        if os.path.exists(output_filepath):
            with open(output_filepath) as self.output_file:
                content = self.output_file.read()
                self.results = json.loads(content)
        else:
            self.results = {}

        try:
            self.client.images.get(self.zap_image_name)
        except ImageNotFound:
            print(f'[-] Image {self.zap_image_name} not exist. pull it first.')
            print(f'[*] Waiting to pull or pull it manually by "docker pull {self.zap_image_name}".')
            self.client.images.pull(self.zap_image_name)
            print(f'[+] Successfully pulled.')

    def create_output(self):
        """
        Save scan results on file
        """
        with open(self.output_filepath, 'w') as self.output_file:
            json.dump(self.results, self.output_file)

    def scan(self):
        """
        Run zap scanner on target
        """
        if not self.client.containers.list(filters={'name': self.zap_container_name}):
            print(f'[*] Running zap container.')
            command = 'zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true'
            self.client.containers.run(
                self.zap_image_name,
                command,
                name=self.zap_container_name,
                ports={'8080/tcp': '8080'},
                auto_remove=True,
                detach=True
            )
            time.sleep(10)
            print(f'[+] Container is up now.')


        print(f'[+] Scan started.')
        results_str = zap_scan.run(self.target)
        self.results[self.target] = json.loads(results_str)
        self.create_output()


def run():
    """
    Run entrypoint.
    """

    parser = argparse.ArgumentParser(description="ZAP")
    parser.add_argument(
        '-t', '--target', dest='target', action='store', required=True,
        help='target that zap scan on it.'
    )
    parser.add_argument(
        '-o', '--output', dest='output_filepath', action='store', default='zap.json',
        help='file to save results. default:"zap.json"'
    )

    args = parser.parse_args()
    zap = ZAP(**vars(args))
    zap.scan()
    print("[+] Done.")


if __name__ == '__main__':
    run()
