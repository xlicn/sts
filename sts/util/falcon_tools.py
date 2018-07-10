import itertools
import json
import os
import shutil
import time

import requests

"""useful tools for Falcon's replay engine"""

class NorthboundSimulator(object):
    '''northbound request sender'''

    def __init__(self):
        self.urlBase = "http://127.0.0.1:8181"
        self.headers = {'content-type': 'application/json'}
        self.auth = ('admin', 'admin')

    def post(self, url, data_dic):
        data = json.dumps(data_dic)
        url = self.urlBase + url
        postRequest = requests.post(url, data, auth=self.auth, headers=self.headers)
        # postRequest.raise_for_status()

    def get(self, url):
        url = self.urlBase + url
        getRequest = requests.get(url, auth=self.auth)
        # getRequest.raise_for_status()

    def put(self, url, data_dic):
        data = json.dumps(data_dic)
        url = self.urlBase + url
        putRequest = requests.put(url, data, auth=self.auth, headers=self.headers)
        # putRequest.raise_for_status()

    def delete(self, url):
        url = self.urlBase + url
        deleteRequest = requests.delete(url, auth=self.auth)
        # deleteRequest.raise_for_status()


class TraceTransformer(object):
    '''transform falcon trace to replay trace'''

    def __init__(self, falcon_trace_path, replay_trace_path):
        self.label_gen = itertools.count(1)
        self.falcon_trace_path = falcon_trace_path
        self.replay_trace_path = replay_trace_path
        self.replay_traces = []

    def buildNBTrace(self, str):
        dict = {
            "fingerprint": ["NorthboundRequest"],
            "dependent_labels": [],
            "prunable": True,
            "timed_out": False,
            "round": 1,
            "class": "NorthboundRequest",
        }

        fields = str.split('+')
        dict['label'] = 'e%d' % self.label_gen.next()
        dict['time'] = [int(fields[2]) / 1000, int(fields[2]) % 1000 * 1000]
        dict['url'] = fields[4]
        dict['method'] = fields[6]
        dict['fingerprint'].append(fields[4])
        dict['fingerprint'].append(fields[6])
        if fields.__len__() > 11:
            dict['data'] = json.loads(fields[10])
        # pprint(dict)
        return json.dumps(dict) + '\n'

    def transform(self):
        fin = open(self.falcon_trace_path, "r")
        fout = open(self.replay_trace_path, "a+")
        try:
            for line in fin.readlines():
                if line[:4] == 'HREQ':
                    fout.write(self.buildNBTrace(line))
        finally:
            fin.close()
            fout.close()


def del_file(path):
    '''delete file tree in a dir'''

    for i in os.listdir(path):
        path_file = os.path.join(path, i)
        if os.path.isfile(path_file):
            os.remove(path_file)
        else:
            del_file(path_file)


def backup(fileName):
    '''send backup rest request to ODL, the backup file is default in karafHome'''

    url = "http://127.0.0.1:8181/restconf/operations/cluster-admin:backup-datastore"
    headers = {'content-type': 'application/json'}
    auth = ('admin', 'admin')
    data_dict = {
        "input": {
            "file-path": fileName
        }
    }
    data = json.dumps(data_dict)
    postRequest = requests.post(url, data, auth=auth, headers=headers)
    postRequest.raise_for_status()


class BackupRestorer(object):
    '''automatic restore ODL from backup file'''

    def __init__(self, backupPath, karafHome):
        if os.path.isfile(backupPath) and os.path.isdir(karafHome):
            self.backupPath = backupPath
            self.karafHome = karafHome
        else:
            raise RuntimeError("wrong backupPath/karafHome")

    def setup(self):
        shutil.copy(self.backupPath, self.karafHome + "/clustered-datastore-restore")
        del_file(self.karafHome + "/journal")
        del_file(self.karafHome + "/snapshots")


if __name__ == '__main__':
    input_path = "/home/xing/code/sts/sts/example_falcon.trace"
    output_path = "/home/xing/code/sts/sts/replay.trace"
    transformer = TraceTransformer(input_path, output_path)
    transformer.transform()

    #backup("datastore_backup")
    time.sleep(5)
    backupPath = "/home/xing/code/rulecleaner/distribution/karaf/target/assembly/datastore_backup"
    karafHome = "/home/xing/code/rulecleaner/distribution/karaf/target/assembly"
    backupRestorer = BackupRestorer(backupPath, karafHome)
    backupRestorer.setup()
