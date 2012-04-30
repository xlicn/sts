# Generated by the protocol buffer compiler.  DO NOT EDIT!

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)


DESCRIPTOR = descriptor.FileDescriptor(
  name='nom_snapshot.proto',
  package='nom_snapshot',
  serialized_pb='\n\x12nom_snapshot.proto\x12\x0cnom_snapshot\"_\n\x06\x41\x63tion\x12-\n\x04type\x18\x01 \x02(\x0e\x32\x1f.nom_snapshot.Action.ActionType\x12\x0c\n\x04port\x18\x02 \x02(\x05\"\x18\n\nActionType\x12\n\n\x06output\x10\x00\"\xd9\x02\n\x05Match\x12\x16\n\x08polarity\x18\x02 \x01(\x08:\x04true\x12\x35\n\rfield_matches\x18\x03 \x03(\x0b\x32\x1e.nom_snapshot.Match.FieldMatch\x1aK\n\nFieldMatch\x12.\n\x05\x66ield\x18\x01 \x01(\x0e\x32\x1f.nom_snapshot.Match.HeaderField\x12\r\n\x05value\x18\x02 \x01(\t\"\xb3\x01\n\x0bHeaderField\x12\n\n\x06\x64l_src\x10\x00\x12\n\n\x06\x64l_dst\x10\x01\x12\x0b\n\x07\x64l_vlan\x10\x02\x12\x0f\n\x0b\x64l_vlan_pcp\x10\x03\x12\x0b\n\x07\x64l_type\x10\x04\x12\n\n\x06nw_tos\x10\x05\x12\x0c\n\x08nw_proto\x10\x06\x12\n\n\x06nw_src\x10\x07\x12\n\n\x06nw_dst\x10\x08\x12\n\n\x06tp_src\x10\t\x12\n\n\x06tp_dst\x10\n\x12\x0b\n\x07in_port\x10\x0b\x12\n\n\x06switch\x10\x0c\"Q\n\x04Rule\x12\"\n\x05match\x18\x01 \x02(\x0b\x32\x13.nom_snapshot.Match\x12%\n\x07\x61\x63tions\x18\x02 \x03(\x0b\x32\x14.nom_snapshot.Action\"9\n\x06Switch\x12\x0c\n\x04\x64pid\x18\x01 \x01(\x05\x12!\n\x05rules\x18\x02 \x03(\x0b\x32\x12.nom_snapshot.Rule\"\x13\n\x04Host\x12\x0b\n\x03mac\x18\x01 \x01(\t\"U\n\x08Snapshot\x12&\n\x08switches\x18\x01 \x03(\x0b\x32\x14.nom_snapshot.Switch\x12!\n\x05hosts\x18\x02 \x03(\x0b\x32\x12.nom_snapshot.Host')



_ACTION_ACTIONTYPE = descriptor.EnumDescriptor(
  name='ActionType',
  full_name='nom_snapshot.Action.ActionType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    descriptor.EnumValueDescriptor(
      name='output', index=0, number=0,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=107,
  serialized_end=131,
)

_MATCH_HEADERFIELD = descriptor.EnumDescriptor(
  name='HeaderField',
  full_name='nom_snapshot.Match.HeaderField',
  filename=None,
  file=DESCRIPTOR,
  values=[
    descriptor.EnumValueDescriptor(
      name='dl_src', index=0, number=0,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='dl_dst', index=1, number=1,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='dl_vlan', index=2, number=2,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='dl_vlan_pcp', index=3, number=3,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='dl_type', index=4, number=4,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='nw_tos', index=5, number=5,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='nw_proto', index=6, number=6,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='nw_src', index=7, number=7,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='nw_dst', index=8, number=8,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='tp_src', index=9, number=9,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='tp_dst', index=10, number=10,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='in_port', index=11, number=11,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='switch', index=12, number=12,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=300,
  serialized_end=479,
)


_ACTION = descriptor.Descriptor(
  name='Action',
  full_name='nom_snapshot.Action',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='type', full_name='nom_snapshot.Action.type', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='port', full_name='nom_snapshot.Action.port', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _ACTION_ACTIONTYPE,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=36,
  serialized_end=131,
)


_MATCH_FIELDMATCH = descriptor.Descriptor(
  name='FieldMatch',
  full_name='nom_snapshot.Match.FieldMatch',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='field', full_name='nom_snapshot.Match.FieldMatch.field', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='value', full_name='nom_snapshot.Match.FieldMatch.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=222,
  serialized_end=297,
)

_MATCH = descriptor.Descriptor(
  name='Match',
  full_name='nom_snapshot.Match',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='polarity', full_name='nom_snapshot.Match.polarity', index=0,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=True, default_value=True,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='field_matches', full_name='nom_snapshot.Match.field_matches', index=1,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_MATCH_FIELDMATCH, ],
  enum_types=[
    _MATCH_HEADERFIELD,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=134,
  serialized_end=479,
)


_RULE = descriptor.Descriptor(
  name='Rule',
  full_name='nom_snapshot.Rule',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='match', full_name='nom_snapshot.Rule.match', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='actions', full_name='nom_snapshot.Rule.actions', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=481,
  serialized_end=562,
)


_SWITCH = descriptor.Descriptor(
  name='Switch',
  full_name='nom_snapshot.Switch',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='dpid', full_name='nom_snapshot.Switch.dpid', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='rules', full_name='nom_snapshot.Switch.rules', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=564,
  serialized_end=621,
)


_HOST = descriptor.Descriptor(
  name='Host',
  full_name='nom_snapshot.Host',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='mac', full_name='nom_snapshot.Host.mac', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=623,
  serialized_end=642,
)


_SNAPSHOT = descriptor.Descriptor(
  name='Snapshot',
  full_name='nom_snapshot.Snapshot',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='switches', full_name='nom_snapshot.Snapshot.switches', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='hosts', full_name='nom_snapshot.Snapshot.hosts', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=644,
  serialized_end=729,
)


_ACTION.fields_by_name['type'].enum_type = _ACTION_ACTIONTYPE
_ACTION_ACTIONTYPE.containing_type = _ACTION;
_MATCH_FIELDMATCH.fields_by_name['field'].enum_type = _MATCH_HEADERFIELD
_MATCH_FIELDMATCH.containing_type = _MATCH;
_MATCH.fields_by_name['field_matches'].message_type = _MATCH_FIELDMATCH
_MATCH_HEADERFIELD.containing_type = _MATCH;
_RULE.fields_by_name['match'].message_type = _MATCH
_RULE.fields_by_name['actions'].message_type = _ACTION
_SWITCH.fields_by_name['rules'].message_type = _RULE
_SNAPSHOT.fields_by_name['switches'].message_type = _SWITCH
_SNAPSHOT.fields_by_name['hosts'].message_type = _HOST

class Action(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _ACTION
  
  # @@protoc_insertion_point(class_scope:nom_snapshot.Action)

class Match(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  
  class FieldMatch(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _MATCH_FIELDMATCH
    
    # @@protoc_insertion_point(class_scope:nom_snapshot.Match.FieldMatch)
  DESCRIPTOR = _MATCH
  
  # @@protoc_insertion_point(class_scope:nom_snapshot.Match)

class Rule(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _RULE
  
  # @@protoc_insertion_point(class_scope:nom_snapshot.Rule)

class Switch(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _SWITCH
  
  # @@protoc_insertion_point(class_scope:nom_snapshot.Switch)

class Host(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _HOST
  
  # @@protoc_insertion_point(class_scope:nom_snapshot.Host)

class Snapshot(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _SNAPSHOT
  
  # @@protoc_insertion_point(class_scope:nom_snapshot.Snapshot)

# @@protoc_insertion_point(module_scope)
