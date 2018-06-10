
from config.experiment_config_lib import ControllerConfig
from sts.topology import MeshTopology
from sts.control_flow.runner import Runner
from sts.input_traces.input_logger import InputLogger
from sts.simulation_state import SimulationConfig

start_cmd = ('''./karaf''')

controllers = [ControllerConfig(start_cmd, cwd="/home/xing/code/controllers/distribution-karaf-0.6.1-Carbon/bin")]

topology_class = MeshTopology
topology_params = "num_switches=3"

simulation_config = SimulationConfig(controller_configs=controllers,
                                     topology_class=topology_class,
                                     topology_params=topology_params)

control_flow = Runner(simulation_config,
                      #halt_on_violation=True,
                      input_logger=InputLogger(),
                      steps=300)
