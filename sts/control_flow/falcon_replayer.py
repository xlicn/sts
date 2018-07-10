# Copyright 2011-2013 Colin Scott
# Copyright 2011-2013 Andreas Wundsam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
control flow for running the simulation forward.
  - Replayer: takes as input a `superlog` with causal dependencies, and
    iteratively prunes until the MCS has been found
'''

import signal

import sts.input_traces.log_parser as log_parser
from sts.control_flow.base import ControlFlow, ReplaySyncCallback
from sts.control_flow.event_scheduler import EventScheduler
from sts.control_flow.interactive import Interactive
from sts.entities import os
from sts.event_dag import EventDag
from sts.falcon_event import *
from sts.input_traces.input_logger import InputLogger
from sts.topology import BufferedPatchPanel
from sts.util.console import color
from sts.util.falcon_tools import TraceTransformer

log = logging.getLogger("FalconReplayer")


class FalconReplayer(ControlFlow):
    '''
    Replay events from a trace

    To set the event scheduling parameters, pass them as keyword args to the
    constructor of this class, which will pass them on to the EventScheduler object it creates.
    '''

    # Interpolated time parameter. *not* the event scheduling epsilon:
    time_epsilon_microseconds = 500

    kwargs = EventScheduler.kwargs | {'create_event_scheduler', 'print_buffers', 'wait_on_deterministic_values',
                                      'default_dp_permit', 'fail_to_interactive',
                                      'fail_to_interactive_on_persistent_violations', 'end_in_interactive',
                                      'input_logger', 'allow_unexpected_messages', 'expected_message_round_window',
                                      'pass_through_whitelisted_messages', 'delay_flow_mods', 'invariant_check_name',
                                      'bug_signature', 'end_wait_seconds', 'transform_dag', 'pass_through_sends',
                                      'fail_fast', 'check_interval'}

    def __init__(self, simulation_cfg, falcon_trace_path, pass_through_whitelisted_messages=True, end_wait_seconds=0.5,
                 pass_through_sends=True, delay_startup=True, delay = 10,  **kwargs):
        '''
         - If invariant_check_name is not None, check it at the end for the
           execution
         - If bug_signature is not None, check whether this particular signature
           appears in the output of the invariant check at the end of the
           execution
        '''
        ControlFlow.__init__(self, simulation_cfg)
        # Label uniquely identifying this replay, set in init_results()
        self.replay_id = "N/A"
        self.logical_time = 0
        self.sync_callback = ReplaySyncCallback(self.get_interpolated_time)

        self.superlog_path = "config/replay.trace"
        transformer = TraceTransformer(falcon_trace_path, "config/replay.trace")
        transformer.transform()
        # The dag is codefied as a list, where each element has
        # a list of its dependents
        self.dag = EventDag(log_parser.parse_path(self.superlog_path))

        if len(self.dag.events) == 0:
            raise ValueError("No events to replay!")

        # compute interpolate to time to be just before first event
        self.compute_interpolated_time(self.dag.events[0])
        # String repesentations of unexpected state changes we've passed through, for
        # statistics purposes.

        self.delay_startup = delay_startup
        self.delay = delay
        self.event_scheduler_stats = None
        self.pass_through_whitelisted_messages = pass_through_whitelisted_messages
        self.pass_through_sends = pass_through_sends
        self._input_logger = InputLogger()
        # How many logical rounds to peek ahead when deciding if a message is
        # expected or not.
        # String repesentations of unexpected messages we've passed through, for
        # statistics purposes.
        self.passed_unexpected_messages = []
        self.end_wait_seconds = end_wait_seconds

        if self.pass_through_whitelisted_messages:
            for event in self.dag.events:
                if hasattr(event, "ignore_whitelisted_packets"):
                    event.ignore_whitelisted_packets = True

        if self.simulation_cfg.ignore_interposition:
            self._ignore_interposition()

        self.create_event_scheduler = \
            lambda simulation: EventScheduler(simulation,
                                              **{k: v for k, v in kwargs.items() if k in EventScheduler.kwargs})

        unknown_kwargs = [k for k in kwargs.keys() if k not in EventScheduler.kwargs]
        if unknown_kwargs != []:
            raise ValueError("Unknown kwargs %s" % str(unknown_kwargs))

    def _log_input_event(self, event, **kws):
        if self._input_logger is not None:
            self._input_logger.log_input_event(event, **kws)

    def _ignore_interposition(self):
        '''
        Configure all interposition points to immediately pass through all
        internal events
        (possibly useful for replays affected by non-determinism)
        '''
        filtered_events = [e for e in self.dag.events if type(e) not in all_internal_events]
        self.dag = EventDag(filtered_events)
        self.default_dp_permit = True
        self.dp_checker = AlwaysAllowDataplane(self.dag)

    def get_interpolated_time(self):
        '''
        During divergence, the controller may ask for the current time more or
        less times than they did in the original run. We control the time, so we
        need to give them some answer. The answers we give them should be
        (i) monotonically increasing, and (ii) between the time of the last
        recorded ("landmark") event and the next landmark event, and (iii)
        as close to the recorded times as possible

        Our temporary solution is to always return the time right before the next
        landmark
        '''
        # TODO(cs): implement Andi's improved time heuristic
        return self.interpolated_time

    def compute_interpolated_time(self, current_event):
        next_time = current_event.time
        just_before_micro = next_time.microSeconds - self.time_epsilon_microseconds
        just_before_micro = max(0, just_before_micro)
        self.interpolated_time = SyncTime(next_time.seconds, just_before_micro)

    def increment_round(self):
        msg.event(color.CYAN + ("Round %d" % self.logical_time) + color.WHITE)

    def init_results(self, results_dir):
        self.replay_id = results_dir
        if self._input_logger:
            self._input_logger.open(results_dir)
        try:
            os.rename(self.superlog_path, results_dir + (self.superlog_path).replace('config', ''))
        finally:
            if os.path.exists(self.superlog_path):
                os.remove(self.superlog_path)

    def simulate(self, post_bootstrap_hook=None):
        ''' Caller *must* call simulation.clean_up() '''

        self.simulation = self.simulation_cfg.bootstrap(self.sync_callback)
        assert (isinstance(self.simulation.patch_panel, BufferedPatchPanel))
        # TODO(aw): remove this hack

        self._log_input_event(ConnectToControllers())
        self.simulation.connect_to_controllers()

        if self.delay_startup:
            # Wait until the first OpenFlow message is received
            log.info("Waiting until first OpenFlow message received..")
            while len(self.simulation.openflow_buffer.pending_receives) == 0:
                self.simulation.io_master.select(self.delay)

        self.simulation.openflow_buffer.pass_through_whitelisted_packets = \
            self.pass_through_whitelisted_messages
        '''
        if self.pass_through_sends:
            self.set_pass_through_sends(self.simulation)
        '''
        self.run_simulation_forward(post_bootstrap_hook)
        time.sleep(60)
        return self.simulation

    def run_simulation_forward(self, post_bootstrap_hook=None):
        event_scheduler = self.create_event_scheduler(self.simulation)
        event_scheduler.set_input_logger(self._input_logger)
        self.event_scheduler_stats = event_scheduler.stats
        if post_bootstrap_hook is not None:
            post_bootstrap_hook()

        def interrupt(sgn, frame):
            msg.interactive("Interrupting replayer, dropping to console (press ^C again to terminate)")
            signal.signal(signal.SIGINT, self.old_interrupt)
            self.old_interrupt = None
            raise KeyboardInterrupt()

        self.old_interrupt = signal.signal(signal.SIGINT, interrupt)

        try:
            for i, event in enumerate(self.dag.events):
                try:
                    self.compute_interpolated_time(event)
                    '''
                    if isinstance(event, InputEvent):
                        self._check_early_state_changes(self.dag, i, event)
                    self._check_new_state_changes(self.dag, i)
                    self._check_unexpected_cp_messages(self.dag, i)
                    '''
                    # TODO(cs): quasi race-condition here. If unexpected state change
                    # happens *while* we're waiting for event, we basically have a
                    # deadlock (if controller logging is set to blocking) until the
                    # timeout occurs
                    # TODO(cs): we don't actually allow new internal message events
                    # through.. we only let new state changes through. Should experiment
                    # with whether we would get better fidelity if we let them through.
                    event_scheduler.schedule(event)
                    if self.logical_time != event.round:
                        self.logical_time = event.round
                        self.increment_round()
                except KeyboardInterrupt:
                    interactive = Interactive(self.simulation_cfg,
                                              input_logger=self._input_logger)
                    interactive.simulate(self.simulation, bound_objects=(('replayer', self),))
                    # If Interactive terminated due to ^D, return to our fuzzing loop,
                    # prepared again to drop into Interactive on ^C.
                    self.old_interrupt = signal.signal(signal.SIGINT, interrupt)
                except Exception:
                    log.critical("Exception raised while scheduling event %s, replay %s"
                                 % (str(event), self.replay_id))
                    raise

        finally:
            if self.old_interrupt:
                signal.signal(signal.SIGINT, self.old_interrupt)
            msg.event(color.B_BLUE + "Event Stats: %s" % str(event_scheduler.stats))


class AlwaysAllowDataplane(object):
    ''' A dataplane checker that always allows through events. Should not be
    used if there are any DataplaneDrops in the trace; in that case, use
    DataplaneChecker
    '''

    def __init__(self, event_dag):
        self.stats = DataplaneCheckerStats(list(event_dag.events))

    def check_dataplane(self, i, simulation):
        for dp_event in simulation.patch_panel.queued_dataplane_events:
            simulation.patch_panel.permit_dp_event(dp_event)


class DataplaneCheckerStats(object):
    ''' Tracks how many drops we actually performed vs. how many we expected to
    perform '''

    def __init__(self, events):
        self.expected_drops = [e.fingerprint for e in events if type(e) == DataplaneDrop]
        self.actual_drops = []

    def record_drop(self, fingerprint):
        self.actual_drops.append(fingerprint)

    def __str__(self):
        ''' Warning: not idempotent! '''
        s = ["Expected drops (%d), Actual drops (%d)" % (len(self.expected_drops),
                                                         len(self.actual_drops))]
        s.append("Missed Drops (expected if TrafficInjections pruned):")
        for drop in self.expected_drops:
            if len(self.actual_drops) == 0 or drop != self.actual_drops[0]:
                s.append("  %s" % str(drop))
            elif len(self.actual_drops) != 0 and drop == self.actual_drops[0]:
                self.actual_drops.pop(0)
        return "\n".join(s)
