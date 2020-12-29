#!/usr/bin/python
#    This file is part of syntheticevtx.
#
#   Copyright 2020 Michael Koll
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Version v. 1.0.0
#
import logging

from Evtx.Nodes import WstringTypeNode, StringTypeNode, SIDTypeNode

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_new_value_length(value_type_node, new_value):
    if isinstance(value_type_node, WstringTypeNode):
        return len(new_value.encode("utf-16le"))
    elif isinstance(value_type_node, StringTypeNode):
        return len(new_value.encode("ascii"))
    elif isinstance(value_type_node, SIDTypeNode):
        # byte version, byte num_elements, dword id_high, dword id_low, elements dword * 4
        return 8 + (len(new_value.split('-')) - 3) * 4
    else:
        raise TypeError("No length handler needed.")