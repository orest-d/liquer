"""Command line interface for liquer."""

from liquer import *
from  pathlib import Path
import sys
import traceback
import argparse
import webbrowser
from liquer.config import load_config, initialize, preset, config

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Liquer command line interface')
    parser.add_argument('--config', '-c', type=str, action="store", help='Configuration file')
    parser.add_argument('--create-config', type=str, action="store", help='Create configuration file')
    parser.add_argument('--find-modules', type=str, action="store", help='Find modules in directory')
    parser.add_argument('--preset', type=str, action="store", help='Set configuration preset')
    parser.add_argument('--query', '-q', type=str, action="store", help='Query to execute')
    parser.add_argument('--output', '-o', type=str, action="store", help='Output directory') 
    parser.add_argument('--serve', '-s', action="store_true", help='Start server')

    args = parser.parse_args()

    if args.config:
        load_config(args.config)
        
    if args.preset:
        conf = config()
        conf["setup"] = conf.get("setup", {})        
        conf["setup"]["preset"] = args.preset

    initialize()

    if args.find_modules:
        preset().find_modules(args.find_modules)
        
    if args.create_config:
        with open(args.create_config,"w") as f:
            f.write(preset().default_config())
            print(f"Configuration file {args.create_config} created.")
        sys.exit(0)

    if args.query:
        query = args.query
        output = args.output
        if output:
            state = evaluate_and_save(query, target_directory=output)
        else:
            state = evaluate(query)

    if args.serve:
        preset().start_server(config())
        