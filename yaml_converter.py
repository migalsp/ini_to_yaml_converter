#!/usr/bin/python
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentTypeError
from configobj import ConfigObj
import yaml
import json
import sys


def getTenantName(config_json, config_keys):
    tenant = dict()
    tenant_name = str()
    tenant_value = str()
    config_keys_list = list(config_keys)

    for key in config_keys_list:
        if '.' not in key:
            if tenant_name != "":
                sys.exit(
                    "The box file has 2 tenants, please the check box ini file")
            else:
                tenant_name = key

    tenant_value = config_json[tenant_name]
    tenant[tenant_name] = tenant_value

    return tenant

def getDefaultValues(config_json, config_keys):
    default_params = dict()
    volume = dict()
    config_keys_list = list(config_keys)

    for key in config_keys_list:

        if key.find("defaults") != -1 and key.find("volume") == -1:
            keys = key.replace("box.defaults.", "")
            for key_item in keys.split('.'):
                default_params.update({key_item: config_json.get(key)})
# TODO: Remove Dynamic volumes for defaults
        elif key.find("defaults") != -1 and key.find("volume") != -1:
            keys = key.replace("box.defaults.", "")
            current_key = keys.split(".")[0]

            for item in config_keys_list:
                if item.find("defaults") != -1 and item.find(current_key) != -1:
                    volume_params = key.replace("box.defaults." + current_key + ".", "")
                    try:
                        volume[current_key].update({volume_params: config_json.get(key)})
                    except KeyError:
                        volume[current_key] = {}
                        volume[current_key].update(
                            {volume_params: config_json.get(key)})

    default = dict(
        defaults=dict(
            default_params,
            volumes=dict(
                volume
            )
        ))
    return default


def getStackValues(config_json, config_keys, stack_name):
    config_keys_list = list(config_keys)
    instance = dict()
    stack_values = {}
    nodes_params_list = []

    for key in config_keys_list:

        if key.find(stack_name) != -1 and key.find("volume") == -1:
            keys = key.replace("box." + stack_name + ".", "")
            instance_num = keys.split(".")[0]
            node_name_key = key.replace("box." + stack_name + "." + instance_num + "." , "")
            node_name = node_name_key.split('.')[0]

            for item in config_keys_list:
                if item.find(stack_name) != -1 and item.find(instance_num) != -1 and item.find(node_name) != -1:
                    instance_params = key.replace(
                        "box." + stack_name + "." + instance_num + "." + node_name + ".", "")
                    try:
                        instance[node_name].update(
                            {instance_params: config_json.get(key)})
                        if "nodename" not in instance[node_name]:
                            instance[node_name]['nodename'] = {}
                            instance[node_name]['nodename'] = node_name
                    except KeyError:
                        instance[node_name] = {}
                        instance[node_name].update(
                            {instance_params: config_json.get(key)})

        elif key.find(stack_name) != -1 and key.find("volume") != -1:
            instance_key = key.replace("box." + stack_name + ".", "")
            instance_num = instance_key.split(".")[0]
            node_name_key = key.replace(
                "box." + stack_name + "." + instance_num + ".", "")
            node_name = node_name_key.split('.')[0]
            node_volume_key = key.replace(
                "box." + stack_name + "." + instance_num + "." + node_name + ".", "")
            node_volume = node_volume_key.split('.')[0]

            for item in config_keys_list:
                if item.find(stack_name) != -1 and item.find(instance_num) != -1 and item.find(node_name) != -1 and item.find(node_volume) != -1:
                    instance_params = key.replace(
                        "box." + stack_name + "." + instance_num + "." + node_name + "." + node_volume + ".", "")
                    try:
                        instance[node_name]['volumes'][node_volume].update(
                            {instance_params: config_json.get(key)})
                    except KeyError:
                        if node_name not in instance:
                            instance[node_name] = {}
                        if "volumes" not in instance[node_name]:
                            instance[node_name]['volumes'] = {}
                        instance[node_name]['volumes'][node_volume] = {}
                        instance[node_name]['volumes'][node_volume].update(
                            {instance_params: config_json.get(key)})

    stack_values[stack_name] = {}
    stack_values[stack_name].update(instance)
    nodes = list(stack_values[stack_name].keys())

    for node_name in nodes:
        if stack_values[stack_name][node_name]['nodename'] == node_name:
            nodes_params_list.append(stack_values[stack_name][node_name])

    stack_values[stack_name] = nodes_params_list

    return stack_values


def getStacks(config_keys):
    stacks = []
    config_keys_list = list(config_keys)
    for key in config_keys_list:
            #keys = key.replace("box.", "")
            try:
                stack_name = key.split(".")[1]
                if stack_name != "defaults":
                    stacks.append(stack_name)
            except IndexError as error:
                pass
    stacks = sorted(set(stacks))
    return stacks


def get_arguments():
    cmd_args = ArgumentParser(
        description="The converter ini box files to yaml",
        formatter_class=ArgumentDefaultsHelpFormatter)

    cmd_args.add_argument(
        "--box", dest="box",
        help="path to box file", required=True)
    cmd_args.add_argument(
        "--save", dest="save",
        help="save to file", required=False, type=str2bool,
        nargs='?', const=True, default=False)
    return cmd_args


def str2bool(string):
    if isinstance(string, bool):
       return string
    if string.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif string.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')

def main(ini_path, save):
    box_params_yaml = {}
    config_json = ConfigObj(ini_path, write_empty_values=False)
    yamlfile = dict()
    config_keys = config_json.viewkeys()

    tenant_name = getTenantName(config_json, config_keys)
    defaults_params = getDefaultValues(config_json, config_keys)
    stacks = getStacks(config_keys)
    box_params_yaml.update(tenant_name)
    box_params_yaml.update(defaults_params)

    for stack in stacks:
        stack_params = getStackValues(config_json, config_keys, stack)
        box_params_yaml.update(stack_params)

    print(box_params_yaml)

    if save :
        yaml_path = ini_path.split('.')[0] + ".yaml"
        yaml_stream = file(yaml_path, 'w')
        yaml.dump(box_params_yaml, yaml_stream, default_flow_style=False)


if __name__ == '__main__':
    cmd_args = get_arguments()
    args = cmd_args.parse_args()

    with open(args.box, 'r') as box_file:
        box = box_file.read()

    box = box.replace('[', '')
    box = box.replace(']', '')
    box_file.close()

    with open(args.box, 'w') as box_file:
        box_file.write(box)
    box_file.close()

    main(args.box, args.save)
