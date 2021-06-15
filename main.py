import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from prometheus_client import Gauge, start_http_server

PORT = int(os.getenv("PORT", "8123"))
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://10.10.2.107:9090")

METRICS: Dict[str, Gauge] = {}
UPDATE_PERIOD = int(os.getenv("UPDATE_PERIOD_S", "60"))


@dataclass(eq=True)
class Tree:
    key: str
    long_key: Optional[str] = None
    index: Optional[str] = None
    value: Optional[int] = None
    unit: Optional[int] = None
    node: Optional[str] = None
    children: List["Tree"] = field(default_factory=list, compare=False)

    def to_dict(self):
        result: Dict[str, Any] = {
            "key": self.key,
        }
        if self.long_key is not None:
            result["long_key"] = self.long_key
        if self.index is not None:
            result["index"] = self.index
        if self.value is not None:
            result["value"] = self.value
        if self.node is not None:
            result["node"] = self.node
        if self.unit is not None:
            result["unit"] = self.unit
        result["children"] = list(map(lambda x: x.to_dict(), self.children))
        return result

    def find_by_index(self, index) -> Optional["Tree"]:
        if self.index == index:
            return self

        for child in self.children:
            result = child.find_by_index(index)
            if result is not None:
                return result
        return None

    def find_by_key(self, key) -> Optional["Tree"]:
        if self.key == key:
            return self

        for child in self.children:
            result = child.find_by_key(key)
            if result is not None:
                return result
        return None

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def flatten(self) -> List["Tree"]:
        if not self.children:
            return [self]

        flattened_children = []
        for child in self.children:
            child.node = self.node
            flattened_children += child.flatten()
        return flattened_children


def fetch_prometheus(url: str):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(
            response.read().decode(
                response.info().get_param("charset") or "utf-8"
            )
        )

    return data["data"]


def build_tree(data: List[Any]) -> Tree:
    root = Tree(".", ".")

    for var in data:
        keys = var["cmcIIIVarName"].split(".")

        current = root
        for index, key in enumerate(keys):
            existings = list(filter(lambda x: x.key == key, current.children))
            if len(existings) > 0:
                current = next(iter(existings))
                continue
            new = Tree(key)
            if index == len(keys) - 1:
                new.index = var["cmcIIIVarIndex"]
                new.long_key = var["cmcIIIVarName"]
            current.children.append(new)
            current = new

    return root


def add_values(root: Tree, data: List[Any]):
    for var in data:
        node = root.find_by_index(var["metric"]["cmcIIIVarIndex"])
        node.value = int(var["value"][1])


def add_units(root: Tree, data: List[Any]):
    for var in data:
        if "cmcIIIVarUnit" in var["metric"]:
            node = root.find_by_index(var["metric"]["cmcIIIVarIndex"])
            node.unit = var["metric"]["cmcIIIVarUnit"]


def filter_values_by_node(
    bindings: List[Any], trees: List[Tree]
) -> List[Tree]:
    result: List[Tree] = []
    for binding in bindings:
        for tree in trees:
            if f"{binding['socket']:02d}" in tree.key:
                tree.node = binding["node"]
                result.append(tree)

    return result


def socket_to_prometheus(socket: Tree):
    new_long_key = "_".join(socket.long_key.lower().split(".")[2:]).replace(
        " ", "_"
    )
    if new_long_key not in METRICS:
        METRICS[new_long_key] = Gauge(
            new_long_key, socket.long_key, ("key", "index", "node")
        )
    METRICS[new_long_key].labels(socket.key, socket.index, socket.node).set(
        socket.value
    )


def fetch_sockets():
    def fetch_var_names() -> List[Any]:
        params = {
            "match[]": 'cmcIIIVarName{cmcIIIVarDeviceIndex="2"}',
        }
        url = f"{PROMETHEUS_URL}/api/v1/series?" + urlencode(params)
        return fetch_prometheus(url)

    tree = build_tree(fetch_var_names())

    def fetch_values() -> List[Any]:
        params = {
            "query": 'cmcIIIVarValueInt{cmcIIIVarDeviceIndex="2"}',
        }
        url = f"{PROMETHEUS_URL}/api/v1/query?" + urlencode(params)
        return fetch_prometheus(url)["result"]

    add_values(tree, fetch_values())

    def fetch_units() -> List[Any]:
        params = {
            "query": 'cmcIIIVarUnit{cmcIIIVarDeviceIndex="2"}',
        }
        url = f"{PROMETHEUS_URL}/api/v1/query?" + urlencode(params)
        return fetch_prometheus(url)["result"]

    add_units(tree, fetch_units())

    def fetch_bindings():
        with open("config.json", "r") as config:
            return json.load(config)["bindings"]

    bindings = fetch_bindings()
    sockets_tree = tree.find_by_key("Sockets")
    return filter_values_by_node(bindings, sockets_tree.children)


def process_data(sockets: List[Tree]):
    new_children: List[Tree] = []
    for socket in sockets:
        new_children.extend(socket.flatten())

    for child in new_children:
        socket_to_prometheus(child)


if __name__ == "__main__":
    start_http_server(PORT)

    while True:
        sockets = fetch_sockets()
        process_data(sockets)
        time.sleep(UPDATE_PERIOD)
