from config.experiment_config_lib import ControllerConfig
from sts.control_flow.runner import Runner
from sts.input_traces.input_logger import InputLogger
from sts.simulation_state import SimulationConfig
from sts.topology import CustomTopology

start_cmd = ('''./karaf''')

controllers = [ControllerConfig(start_cmd, cwd="/home/xing/code/controllers/distribution-karaf-0.6.1-Carbon/bin")]

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

control_flow = Runner(simulation_config,
                      # halt_on_violation=True,
                      input_logger=InputLogger(),
                      steps=300)


def main(topology_params):
    if topology_params.has_key('hosts'):
        print(topology_params.get('hosts'))


if __name__ == "__main__":
    # topology = eval("%s(%s,create_io_worker=create_io_worker)" % (topology_class.__name__, topology_params))
    eval("main(topology_params)")
    CustomTopology(topology_params)
    # print(topology_params)
