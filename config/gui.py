from config.experiment_config_lib import ControllerConfig
from sts.topology import FatTree, BufferedPatchPanel
from sts.control_flow.interactive import Interactive
from sts.input_traces.input_logger import InputLogger
from sts.simulation_state import SimulationConfig

# Use POX as our controller
start_cmd = "./pox.py --no-cli --verbose openflow.of_01 --address=__address__ --port=__port__ sts.syncproto.pox_syncer samples.topo forwarding.l2_learning"
controllers = [ControllerConfig(start_cmd, cwd="/home/xing/code/controllers/pox", address="127.0.0.1", port=8888, sync="tcp:localhost:18888")]
topology_class = FatTree
topology_params = "num_pods=2, gui=True"
dataplane_trace = "dataplane_traces/ping_pong_same_subnet.trace"

simulation_config = SimulationConfig(controller_configs=controllers,
                                     topology_class=topology_class,
                                     topology_params=topology_params,
                                     dataplane_trace=dataplane_trace)

control_flow = Interactive(simulation_config, input_logger=InputLogger())
