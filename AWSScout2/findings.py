#
from AWSScout2.utils import *

# Import opinel
from opinel.utils import *

# Import stock packages
import copy
import fnmatch
import os
import re


########################################
# Globals
########################################

finding_levels = ['danger', 'warning']


########################################
# Common functions
########################################

def change_level(level):
    if prompt_4_yes_no('Would you like to change the default level (%s)' % level):
        return prompt_4_value('Enter the level: ', finding_levels, level)
    else:
        return level

#
# Load a ruleset from a JSON file
#
def load_ruleset(ruleset_filename, quiet = False):
    if not os.path.exists(ruleset_filename):
        if not quiet:
            printError('Error: the file %s does not exist.' % ruleset_filename)
        return None
    try:
        with open(ruleset_filename, 'rt') as f:
            ruleset = json.load(f)
    except Exception as e:
        printException(e)
        printError('Error: ruleset file %s contains malformed JSON.' % ruleset_filename)
        return None
    return ruleset

#
# Initialize rules based on ruleset and services in scope
#
def init_rules(ruleset, services, environment_name, ip_ranges, aws_account_id, generator = False, rule_type = 'rules'):
    # Load rules from JSON files
    rules = {}
    for rule_metadata in ruleset['rules']:
        # Skip disabled rules
        if 'enabled' in rule_metadata and rule_metadata['enabled'] in ['false', 'False', False] and not generator:
            continue
        # Skip rules that apply to an out-of-scope service
        rule_details = load_config_from_json(rule_metadata, ip_ranges, aws_account_id, rule_type)
        if not rule_details:
            continue
        if 'enabled' in rule_metadata and rule_metadata['enabled']:
            rule_details['enabled'] = True
        skip_rule = True
        for service in services:
            if rule_details['path'].startswith(service):
                skip_rule = False
        if skip_rule:
            continue
        # Build the rules dictionary
        path = rule_details['path']
        manage_dictionary(rules, path, {})
        if 'level' in rule_metadata:
            rule_details['level'] = rule_metadata['level']
        key = rule_details['key'] if 'key' in rule_details else rule_metadata['filename']
        # Set condition operator
        if not 'condition_operator' in rule_details:
            rule_details['condition_operator'] = 'and'
        # Save details for rule
        key = key.replace('.json', '')
        rules[path][key] = rule_details
    return rules

#
# Search for an existing ruleset that matches the environment name
#
def search_ruleset(scout2_dir, environment_name):
    scout2_rulesets_ditr = '%s/%s' % (scout2_dir, RULESETS_DIR)
    if environment_name != 'default':
        ruleset_found = False
        for f in os.listdir(scout2_rulesets_dir):
            if fnmatch.fnmatch(f, '*.' + environment_name + '.json'):
                ruleset_found = True
        if ruleset_found and prompt_4_yes_no("A ruleset whose name matches your environment name (%s) was found. Would you like to use it instead of the default one" % environment_name):
            pass
        else:
            environment_name = default
    return '%s/%s.json' % (scout2_rulesets_dir, environment_name)

def set_arguments(arg_names, t):
    real_args = []
    for a in arg_names:
        real_args.append(set_argument_values(a, t))
    return real_args

def set_argument_values(parameterized_input, target, convert = False):
    if convert:
        parameterized_input = json.dumps(parameterized_input)
    args = re.findall(r'(_ARG_(\w+)_)', parameterized_input)
    for arg in args:
        index = int(arg[1])
        parameterized_input = parameterized_input.replace(arg[0], target[index])
    return json.loads(parameterized_input) if convert else parameterized_input

def set_description(string, description):
    attributes = re.findall(r'(_(\w+)_)', string)
    for attribute in attributes:
        name = attribute[1].lower()
        if name == 'description':
            string = string.replace(attribute[0], description)
        else:
            printError('The field %s is not supported yet for injection in the questions')
    return string

