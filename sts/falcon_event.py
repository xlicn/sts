# Copyright 2011-2013 Colin Scott
# Copyright 2011-2013 Andreas Wundsam
# Copyright 2012-2013 Sam Whitlock
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
Classes representing events to be replayed. These events can be serialized to
events.trace JSON files.

Note about the JSON events.trace format:

All events are serialized to JSON with the Event.to_json() method.

All events have a fingerprint field, which is used to compute functional
equivalence between events across different replays of the trace.

The default format of the fingerprint field is a tuple (event class name,).

The specific format of the fingerprint field is documented in each class'
fingerprint() method.

The format of other additional fields is documented in
each event's __init__() method.
'''

import abc
import itertools
import json
import marshal
import types

from config.invariant_checks import name_to_invariant_check
from pox.lib.util import TimeoutError
from sts.dataplane_traces.trace import DataplaneEvent
from sts.entities import Link
from sts.fingerprints.messages import *
from sts.syncproto.base import SyncTime
from sts.util.console import msg
from sts.util.falcon_tools import NorthboundSimulator

log = logging.getLogger("events")


def dictify_fingerprint(fingerprint):
    # Hack: convert Fingerprint objects into Fingerprint.to_dict()
    mutable = list(fingerprint)
    for i, e in enumerate(mutable):
        if isinstance(mutable[i], Fingerprint):
            mutable[i] = mutable[i].to_dict()
    return tuple(mutable)


class Event(object):
    ''' Superclass for all event types. '''
    __metaclass__ = abc.ABCMeta

    # Create unique labels for events
    _label_gen = itertools.count(1)
    # Ensure globally unique labels
    _all_label_ids = set()

    def __init__(self, prefix="e", label=None, round=-1, time=None, dependent_labels=None,
                 prunable=True):
        if label is None:
            label_id = Event._label_gen.next()
            label = prefix + str(label_id)
            while label_id in Event._all_label_ids:
                label_id = Event._label_gen.next()
                label = prefix + str(label_id)
        if time is None:
            # TODO(cs): compress time for interactive mode?
            time = SyncTime.now()
        self.label = label
        Event._all_label_ids.add(int(label[1:]))
        self.round = round
        self.time = time
        # Add on dependent labels to appease log_processing.superlog_parser.
        # TODO(cs): Replayer shouldn't depend on superlog_parser
        self.dependent_labels = dependent_labels if dependent_labels else []
        # Whether this event should be prunable by MCSFinder. Initialization
        # inputs are not pruned.
        self.prunable = True
        # Whether the (internal) event timed out in the most recent round
        self.timed_out = False

    @property
    def label_id(self):
        return int(self.label[1:])

    @property
    def fingerprint(self):
        ''' All events must have a fingerprint. Fingerprints are used to compute
        functional equivalence. '''
        return (self.__class__.__name__,)

    @abc.abstractmethod
    def proceed(self, simulation):
        '''Executes a single `round'. Returns a boolean that is true if the
        Replayer may continue to the next Event, otherwise proceed() again
        later.'''
        pass

    def to_json(self):
        ''' Convert the event to json format '''
        fields = dict(self.__dict__)
        fields['class'] = self.__class__.__name__
        # fingerprints are accessed through @property, not in __dict__:
        fields['fingerprint'] = dictify_fingerprint(self.fingerprint)
        if '_fingerprint' in fields:
            del fields['_fingerprint']
        return json.dumps(fields)

    def __hash__(self):
        # Assumption: labels are unique
        return self.label.__hash__()

    def __eq__(self, other):
        # Assumption: labels are unique
        if type(self) != type(other):
            return False
        return self.label == other.label

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.__class__.__name__ + ":" + self.label

    def __repr__(self):
        s = self.__class__.__name__ + ":" + self.label \
            + ":" + str(self.fingerprint)
        return s


class InputEvent(Event):
    '''An InputEvents is an event that the simulator injects into the simulation.

    Each InputEvent has a list of dependent InternalEvents that it takes in its
    constructor. This enables us to properly prune events.

    `InputEvents' may also be referred to as 'external
    events', elsewhere in documentation or code.'''

    def __init__(self, label=None, round=-1, time=None, dependent_labels=None,
                 prunable=True):
        super(InputEvent, self).__init__(prefix='e', label=label, round=round, time=time,
                                         dependent_labels=dependent_labels,
                                         prunable=prunable)


# --------------------------------- #
#  Concrete classes of InputEvents  #
# --------------------------------- #

def assert_fields_exist(json_hash, *args):
    ''' assert that the fields exist in json_hash '''
    fields = args
    for field in fields:
        if field not in json_hash:
            raise ValueError("Field %s not in json_hash %s" % (field, str(json_hash)))


def extract_label_time(json_hash):
    assert_fields_exist(json_hash, 'label', 'time', 'round')
    label = json_hash['label']
    time = SyncTime(json_hash['time'][0], json_hash['time'][1])
    round = json_hash['round']
    return (label, time, round)


class ConnectToControllers(InputEvent):
    ''' Logged at the beginning of the execution. Causes all switches to open
    TCP connections their their parent controller(s).
    '''

    def __init__(self, label=None, round=-1, time=None,
                 timeout_disallowed=True):
        super(ConnectToControllers, self).__init__(label=label, round=round, time=time)
        self.prunable = False
        # timeout_disallowed is only for backwards compatibility
        self.timeout_disallowed = timeout_disallowed

    def proceed(self, simulation):
        simulation.connect_to_controllers()
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round, timeout_disallowed) = extract_base_fields(json_hash)
        return ConnectToControllers(label=label, time=time, round=round,
                                    timeout_disallowed=timeout_disallowed)


class NorthboundRequest(InputEvent):
    '''Send a RESTful request from nb simulator'''

    def __init__(self, label=None, round=-1, time=None, url=None, method=None, data=None):
        super(NorthboundRequest, self).__init__(label=label, round=round, time=time)
        self.url = url
        self.method = method
        self.data = data

    def proceed(self, simulation):
        nb_simulator = NorthboundSimulator()
        if self.method == 'GET':
            nb_simulator.get(self.url)
        elif self.method == 'POST':
            nb_simulator.post(self.url, self.data)
        elif self.method == 'PUT':
            nb_simulator.put(self.url, self.data)
        elif self.method == 'DELETE':
            nb_simulator.delete(self.url)
        else:
            raise RuntimeError("Method not supported")
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'url')
        assert_fields_exist(json_hash, 'method')
        url = str(json_hash['url'])
        method = str(json_hash['method'])
        data = json_hash['data']
        return NorthboundRequest(label=label, round=round, time=time, url=url, method=method, data=data)

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format: (class name, url, method) '''
        return (self.__class__.__name__, self.url, self.method)


class SwitchFailure(InputEvent):
    ''' Crashes a switch, by disconnecting its TCP connection with the
    controller(s).'''

    def __init__(self, dpid, label=None, round=-1, time=None):
        '''
        Parameters:
         - dpid: unique integer identifier of the switch.
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
        '''
        super(SwitchFailure, self).__init__(label=label, round=round, time=time)
        self.dpid = dpid

    def proceed(self, simulation):
        software_switch = simulation.topology.get_switch(self.dpid)
        simulation.topology.crash_switch(software_switch)
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'dpid')
        dpid = int(json_hash['dpid'])
        return SwitchFailure(dpid, label=label, round=round, time=time)

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format: (class name, dpid) '''
        return (self.__class__.__name__, self.dpid,)


class SwitchRecovery(InputEvent):
    ''' Recovers a crashed switch, by reconnecting its TCP connection with the
    controller(s).'''

    def __init__(self, dpid, label=None, round=-1, time=None):
        '''
        Parameters:
         - dpid: unique integer identifier of the switch.
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
        '''
        super(SwitchRecovery, self).__init__(label=label, round=round, time=time)
        self.dpid = dpid

    def proceed(self, simulation):
        software_switch = simulation.topology.get_switch(self.dpid)
        try:
            down_controller_ids = map(lambda c: c.cid,
                                      simulation.controller_manager.down_controllers)

            simulation.topology.recover_switch(software_switch,
                                               down_controller_ids=down_controller_ids)
        except TimeoutError:
            # Controller is down... Hopefully control flow will notice soon enough
            log.warn("Timed out on %s" % str(self.fingerprint))
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'dpid')
        dpid = int(json_hash['dpid'])
        return SwitchRecovery(dpid, round=round, label=label, time=time)

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format: (class name, dpid) '''
        return (self.__class__.__name__, self.dpid,)


def get_link(link_event, simulation):
    start_software_switch = simulation.topology.get_switch(link_event.start_dpid)
    end_software_switch = simulation.topology.get_switch(link_event.end_dpid)
    link = Link(start_software_switch, link_event.start_port_no,
                end_software_switch, link_event.end_port_no)
    return link


class LinkFailure(InputEvent):
    ''' Cuts a link between switches. This causes the switch to send an
    ofp_port_status message to its parent(s). All packets forwarded over
    this link will be dropped until a LinkRecovery occurs.'''

    def __init__(self, start_dpid, start_port_no, end_dpid, end_port_no,
                 label=None, round=-1, time=None):
        '''
        Parameters:
         - start_dpid: unique integer identifier of the first switch connected to the link.
         - start_port_no: integer port number of the start switch's port.
         - end_dpid: unique integer identifier of the second switch connected to the link.
         - end_port_no: integer port number of the end switch's port to be created.
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
        '''
        super(LinkFailure, self).__init__(label=label, round=round, time=time)
        self.start_dpid = start_dpid
        self.start_port_no = start_port_no
        self.end_dpid = end_dpid
        self.end_port_no = end_port_no

    def proceed(self, simulation):
        link = get_link(self, simulation)
        simulation.topology.sever_link(link)
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'start_dpid', 'start_port_no', 'end_dpid',
                            'end_port_no')
        start_dpid = int(json_hash['start_dpid'])
        start_port_no = int(json_hash['start_port_no'])
        end_dpid = int(json_hash['end_dpid'])
        end_port_no = int(json_hash['end_port_no'])
        return LinkFailure(start_dpid, start_port_no, end_dpid, end_port_no,
                           round=round, label=label, time=time)

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format:
        (class name, start dpid, start port_no, end dpid, end port_no) '''
        return (self.__class__.__name__,
                self.start_dpid, self.start_port_no,
                self.end_dpid, self.end_port_no)


class LinkRecovery(InputEvent):
    ''' Recovers a failed link between switches. This causes the switch to send an
    ofp_port_status message to its parent(s). '''

    def __init__(self, start_dpid, start_port_no, end_dpid, end_port_no,
                 label=None, round=-1, time=None):
        '''
        Parameters:
         - start_dpid: unique integer identifier of the first switch connected to the link.
         - start_port_no: integer port number of the start switch's port.
         - end_dpid: unique integer identifier of the second switch connected to the link.
         - end_port_no: integer port number of the end switch's port to be created.
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
        '''
        super(LinkRecovery, self).__init__(label=label, round=round, time=time)
        self.start_dpid = start_dpid
        self.start_port_no = start_port_no
        self.end_dpid = end_dpid
        self.end_port_no = end_port_no

    def proceed(self, simulation):
        link = get_link(self, simulation)
        simulation.topology.repair_link(link)
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'start_dpid', 'start_port_no', 'end_dpid',
                            'end_port_no')
        start_dpid = int(json_hash['start_dpid'])
        start_port_no = int(json_hash['start_port_no'])
        end_dpid = int(json_hash['end_dpid'])
        end_port_no = int(json_hash['end_port_no'])
        return LinkRecovery(start_dpid, start_port_no, end_dpid, end_port_no,
                            round=round, label=label, time=time)

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format:
        (class name, start dpid, start port, end dpid, end port)
        '''
        return (self.__class__.__name__,
                self.start_dpid, self.start_port_no,
                self.end_dpid, self.end_port_no)


class TrafficInjection(InputEvent):
    ''' Injects a dataplane packet into the network at the given host's access link '''

    def __init__(self, label=None, dp_event=None, host_id=None, round=-1, time=None, prunable=True):
        '''
        Parameters:
         - dp_event: DataplaneEvent object encapsulating the packet contents and the
           access link.
         - host_id: unique integer label identifying the host that generated the
           packet.
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
         - prunable: whether this input event can be pruned during delta
           debugging.
        '''
        super(TrafficInjection, self).__init__(label=label, round=round, time=time,
                                               prunable=prunable)
        self.dp_event = dp_event
        self.host_id = host_id

    def proceed(self, simulation):
        # If dp_event is None, backwards compatibility
        if self.dp_event is None:
            if simulation.dataplane_trace is None:
                raise RuntimeError("No dataplane trace specified!")
            simulation.dataplane_trace.inject_trace_event()
        else:
            host = simulation.topology.link_tracker \
                .interface2access_link[self.dp_event.interface].host
            host.send(self.dp_event.interface, self.dp_event.packet)
        return True

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format: (class name, dp event, host_id)
        The format of dp event is:
        {"interface": HostInterface.to_json(), "packet": base 64 encoded packet contents}
        See entities.py for the HostInterface json format.
        '''
        return (self.__class__.__name__, self.dp_event, self.host_id)

    def to_json(self):
        fields = {}
        fields = dict(self.__dict__)
        fields['class'] = self.__class__.__name__
        fields['dp_event'] = self.dp_event.to_json()
        fields['fingerprint'] = (self.__class__.__name__, self.dp_event.to_json(), self.host_id)
        fields['host_id'] = self.host_id
        return json.dumps(fields)

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        prunable = True
        if 'prunable' in json_hash:
            prunable = json_hash['prunable']
        dp_event = None
        if 'dp_event' in json_hash:
            dp_event = DataplaneEvent.from_json(json_hash['dp_event'])
        host_id = None
        if 'host_id' in json_hash:
            host_id = json_hash['host_id']
        return TrafficInjection(label=label, dp_event=dp_event, host_id=host_id, time=time, round=round,
                                prunable=prunable)


class WaitTime(InputEvent):
    ''' Causes the simulation to sleep for the specified number of seconds.
    Controller processes continue running during this time.'''

    def __init__(self, wait_time, label=None, round=-1, time=None):
        '''
        Parameters:
         - wait_time: float representing how long to sleep in seconds.
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
        '''
        super(WaitTime, self).__init__(label=label, round=round, time=time)
        self.wait_time = wait_time

    def proceed(self, simulation):
        log.info("WaitTime: pausing simulation for %f seconds" % (self.wait_time))
        time.sleep(self.wait_time)
        return True

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'wait_time')
        wait_time = json_hash['wait_time']
        return WaitTime(wait_time, round=round, label=label, time=time)


class CheckInvariants(InputEvent):
    ''' Causes the simulation to pause itself and check the given invariant before
    proceeding. '''

    def __init__(self, label=None, round=-1, time=None,
                 invariant_check_name="InvariantChecker.check_correspondence"):
        '''
        Parameters:
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
         - invariant_check_name: unique name of the invariant to be checked. See
           config.invariant_checks for an exhaustive list of possible invariant
           checks.
        '''
        super(CheckInvariants, self).__init__(label=label, round=round, time=time)
        # For backwards compatibility.. (invariants used to be specified as
        # marshalled functions, not invariant check names)
        self.legacy_invariant_check = not isinstance(invariant_check_name, basestring)
        if self.legacy_invariant_check:
            self.invariant_check = invariant_check_name
        else:
            # Otherwise, invariant check is specified as a name
            self.invariant_check_name = invariant_check_name
            if invariant_check_name not in name_to_invariant_check:
                raise ValueError('''Unknown invariant check %s.\n'''
                                 '''Invariant check name must be defined in config.invariant_checks''',
                                 invariant_check_name)
            self.invariant_check = name_to_invariant_check[invariant_check_name]

    def proceed(self, simulation):
        try:
            violations = self.invariant_check(simulation)
            simulation.violation_tracker.track(violations, self.round)
            persistent_violations = simulation.violation_tracker.persistent_violations
        except NameError as e:
            raise ValueError('''Closures are unsupported for invariant check '''
                             '''functions.\n Use dynamic imports inside of your '''
                             '''invariant check code and define all globals '''
                             '''locally.\n NameError: %s''' % str(e))
        if violations != []:
            msg.fail("The following correctness violations have occurred: %s" % str(violations))
            if hasattr(simulation, "fail_to_interactive") and simulation.fail_to_interactive:
                raise KeyboardInterrupt("fail to interactive")
        else:
            msg.success("No correctness violations!")
        if persistent_violations != []:
            msg.fail("Persistent violations detected!: %s" % str(persistent_violations))
            if hasattr(simulation, "fail_to_interactive_on_persistent_violations") and \
                    simulation.fail_to_interactive_on_persistent_violations:
                raise KeyboardInterrupt("fail to interactive on persistent violation")
        return True

    def to_json(self):
        fields = dict(self.__dict__)
        fields['class'] = self.__class__.__name__
        if self.legacy_invariant_check:
            fields['invariant_check'] = marshal.dumps(self.invariant_check.func_code) \
                .encode('base64')
            fields['invariant_name'] = self.invariant_check.__name__
        else:
            fields['invariant_name'] = self.invariant_check_name
            fields['invariant_check'] = None
        fields['fingerprint'] = "N/A"
        return json.dumps(fields)

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        invariant_check_name = "InvariantChecker.check_connectivity"
        if 'invariant_name' in json_hash:
            invariant_check_name = json_hash['invariant_name']
        elif 'invariant_check' in json_hash:
            # Legacy code (marshalled function)
            # Assumes that the closure is empty
            code = marshal.loads(json_hash['invariant_check'].decode('base64'))
            invariant_check_name = types.FunctionType(code, globals())

        return CheckInvariants(label=label, time=time, round=round,
                               invariant_check_name=invariant_check_name)


class DataplaneDrop(InputEvent):
    ''' Removes an in-flight dataplane packet with the given fingerprint from
    the network. '''

    def __init__(self, fingerprint, label=None, host_id=None, dpid=None, round=-1, time=None, passive=True):
        '''
        Parameters:
         - label: a unique label for this event. Internal event labels begin with 'i'
           and input event labels begin with 'e'.
         - host_id: unique integer label identifying the host that generated the
           packet. May be None.
         - dpid: unique integer identifier of the switch. May be None.
         - time: the timestamp of when this event occured. Stored as a tuple:
           [seconds since unix epoch, microseconds].
         - round: optional integer. Indicates what simulation round this event occured
           in.
         - passive: whether we're using Replayer.DataplaneChecker
        '''
        super(DataplaneDrop, self).__init__(label=label, round=round, time=time)
        # N.B. fingerprint is monkeypatched on to DpPacketOut events by BufferedPatchPanel
        if fingerprint[0] != self.__class__.__name__:
            fingerprint = list(fingerprint)
            fingerprint.insert(0, self.__class__.__name__)
        if type(fingerprint) == list:
            fingerprint = (fingerprint[0], DPFingerprint(fingerprint[1]),
                           fingerprint[2], fingerprint[3])
        self._fingerprint = fingerprint
        # TODO(cs): passive is a bit of a hack, but this was easier.
        self.passive = passive
        self.host_id = host_id
        self.dpid = dpid

    def proceed(self, simulation):
        # Handled by control_flow.replayer.DataplaneChecker
        if self.passive:
            return True
        else:
            dp_event = simulation.patch_panel.get_buffered_dp_event(self.fingerprint[1:])
            if dp_event is not None:
                simulation.patch_panel.drop_dp_event(dp_event)
                return True
            return False

    @property
    def fingerprint(self):
        ''' Fingerprint tuple format:
        (class name, DPFingerprint, switch dpid, port no)
        See fingerprints/messages.py for format of DPFingerprint.
        '''
        return self._fingerprint

    @property
    def dp_fingerprint(self):
        return self.fingerprint[1]

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'fingerprint')
        fingerprint = json_hash['fingerprint']
        return DataplaneDrop(fingerprint, round=round, label=label, time=time)

    def to_json(self):
        fields = dict(self.__dict__)
        fields['class'] = self.__class__.__name__
        fields['fingerprint'] = (self.fingerprint[0], self.fingerprint[1].to_dict(),
                                 self.fingerprint[2], self.fingerprint[3])
        del fields['_fingerprint']
        return json.dumps(fields)


# TODO(cs): Temporary hack until we figure out determinism
class LinkDiscovery(InputEvent):
    ''' Deprecated '''

    def __init__(self, controller_id, link_attrs, label=None, round=-1, time=None):
        super(LinkDiscovery, self).__init__(label=label, round=round, time=time)
        self._fingerprint = (self.__class__.__name__,
                             controller_id, tuple(link_attrs))
        self.controller_id = controller_id
        self.link_attrs = link_attrs

    def proceed(self, simulation):
        controller = simulation.controller_manager.get_controller(self.controller_id)
        controller.sync_connection.send_link_notification(self.link_attrs)
        return True

    @property
    def fingerprint(self):
        return self._fingerprint

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        assert_fields_exist(json_hash, 'controller_id', 'link_attrs')
        controller_id = json_hash['controller_id']
        link_attrs = json_hash['link_attrs']
        return LinkDiscovery(controller_id, link_attrs, round=round, label=label, time=time)


class NOPInput(InputEvent):
    ''' Does nothing. Useful for fenceposting. '''

    def proceed(self, simulation):
        return True

    @property
    def fingerprint(self):
        return (self.__class__.__name__,)

    @staticmethod
    def from_json(json_hash):
        (label, time, round) = extract_label_time(json_hash)
        return NOPInput(round=round, label=label, time=time)


# N.B. When adding inputs to this list, make sure to update input susequence
# validity checking in event_dag.py.
all_input_events = [NorthboundRequest, SwitchFailure, SwitchRecovery, LinkFailure, LinkRecovery, TrafficInjection,
                    WaitTime,
                    CheckInvariants, DataplaneDrop, LinkDiscovery, ConnectToControllers, NOPInput]


def extract_base_fields(json_hash):
    (label, time, round) = extract_label_time(json_hash)
    timeout_disallowed = False
    if 'timeout_disallowed' in json_hash:
        timeout_disallowed = json_hash['timeout_disallowed']
    return (label, time, round, timeout_disallowed)


all_events = all_input_events
all_internal_events = []
all_special_events = []
dp_events = {DataplaneDrop}
