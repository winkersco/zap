import argparse
import json
import os
import sys

import docker
from docker.errors import ImageNotFound, DockerException


class ZAP:
    def __init__(self, target, output_filepath):

        try:
            self.client = docker.from_env()
        except DockerException:
            print(f'[-] Cannot find api. maybe docker is not running.')
            sys.exit(-1)
        self.results = {}
        self.target = target
        self.output_filepath = output_filepath
        self.zap_image_name = 'owasp/zap2docker-stable'

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
        with open(self.output_filepath, 'w') as self.output_file:
            json.dump(self.results, self.output_file)

    def get_processed_results(self, raw_results):
        processed_results = []
        for technology in raw_results['technologies']:
            name = technology['name']
            slug = technology['slug']
            version = technology['version']
            confidence = technology['confidence']

            category_dict = technology['categories'][0]
            category_id = category_dict['id']
            category_name = category_dict['name']
            category_slug = category_dict['slug']
            category = {
                'id': category_id,
                'name': category_name,
                'slug': category_slug
            }

            result = {
                'name': name,
                'slug': slug,
                'version': version,
                'confidence': confidence,
                'category': category,
            }
            processed_results.append(result)
        return processed_results

    def scan(self):
        print(f'[*] Running zap container.')
        container = self.client.containers.run(self.zap_image_name, self.target, auto_remove=True)
        raw_results = json.loads(container.decode())
        self.results[self.target] = self.get_processed_results(raw_results)
        self.create_output()


def run():
    """Run entrypoint."""

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
    print('[+] Done.')


if __name__ == '__main__':
    run()
