from config.experiment_config_lib import ControllerConfig
from sts.control_flow.falcon_replayer import FalconReplayer
from sts.simulation_state import SimulationConfig
from sts.topology import CustomTopology

controllers = [ControllerConfig(start_cmd='./karaf', label='c1', address='127.0.0.1',
                                cwd='/home/xing/code/controllers/distribution-karaf-0.6.1-Carbon/bin')]

topology_class = CustomTopology
topology_params = {
    'hosts': ['h1', 'h2', 'h3', 'h4', 'h5'],
    'switches': ['s1', 's2', 's3', 's4'],
    'access_links': [('h1', 's1'), ('h2', 's1'), ('h3', 's2'), ('h4', 's2'), ('h5', 's3')],
    'internal_links': [('s1', 's2'), ('s2', 's4'), ('s1', 's4'), ('s3', 's4')]
}

simulation_config = SimulationConfig(controller_configs=controllers,
                                     topology_class=topology_class,
                                     topology_params=topology_params)

falcon_trace_path = "/home/xing/code/sts/config/example_falcon.trace"
backupPath = "/home/xing/code/rulecleaner/distribution/karaf/target/assembly/datastore_backup"
karafHome = "/home/xing/code/rulecleaner/distribution/karaf/target/assembly"

control_flow = FalconReplayer(simulation_config, falcon_trace_path)
