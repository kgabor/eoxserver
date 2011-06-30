#!/usr/bin/python

import argparse
import tempfile
import shutil
import os
import sys

TAG_PATH_SRC = "<$PATH_SRC$>"
TAG_PATH_DST = "<$PATH_DST$>"
TAG_INSTANCE_ID = "<$INSTANCE_ID$>"
TAG_MAPSCRIPT = "<$MAPSCRIPT_PATH$>"

"""def copy_file(src_pth, dst_pth):
    dirname, filename = os.path.split(dst_pth)
    print(dirname, filename)
    shutil.copy(src_pth, dirname)
    os.rename(os.path.join(dirname, os.path.basename(src_pth)),
              os.path.join(dirname, filename))
    
"""
def copy_and_replace_tags(src_pth, dst_pth, replacements):
    """Helper function to copy a file and replace tags within a file."""
    
    new_file = open(dst_pth,'w')
    old_file = open(src_pth)
    for line in old_file:
        for pattern, subst in replacements.items():
            line = line.replace(pattern, subst)
        new_file.write(line)

    new_file.close()
    old_file.close()

def create_file(dir_or_path, file=None):
    if file is not None:
        dir_or_path = os.path.join(dir_or_path, file)
    f = open(dir_or_path, 'w')
    f.close()

def run(args):
    parser = argparse.ArgumentParser()
    parser.description = """Create a new EOxServer instance. This instance 
                         will create a root directory with the instance name in
                         the given (optional) directory.

                         If the --init_spatialite flag is set, then the initial
                         database will be created and initialized.
                         """
                         
    parser.add_argument('-d', '--dir', default='.',
                        help='Optional base directory. Defaults to the current directory.')
    parser.add_argument('--initial_data', metavar='DIR', default=False,
                        help='Not yet used')
    parser.add_argument('--init_spatialite', action='store_true',
                        help='Flag to initialize the sqlite database.')
    parser.add_argument('--mapscript-dir', default=False,
                        metavar='DIR',
                        help='Optional path to the MapServer mapscript library.')
    parser.add_argument('instance_id', nargs=1, action='store',
                        metavar='INSTANCE_ID',
                        help='Mandatory name of the eoxserver instance')
    
    args = parser.parse_args(args)

    instance_id = args.instance_id[0]
    dst_root_dir = os.path.abspath(args.dir)
    dst_inst_dir = os.path.join(dst_root_dir, instance_id)
    dst_conf_dir = os.path.join(dst_inst_dir, "conf")
    dst_data_dir = os.path.join(dst_inst_dir, "data")
    dst_logs_dir = os.path.join(dst_inst_dir, "logs")
    dst_fixtures_dir = os.path.join(dst_data_dir, "fixtures")

    src_root_dir = os.path.dirname(os.path.abspath(__file__))
    src_conf_dir = os.path.join(src_root_dir, "conf")

    if args.initial_data:
        initial_data = os.path.abspath(args.initial_data)

    # run django-admin.py startproject

    os.chdir(dst_root_dir)

    print("Initializing django project.")
    assert(os.system("django-admin.py startproject %s" % instance_id) == 0)

    # create the `conf` subdirectory
    os.mkdir(dst_conf_dir)
    os.mkdir(dst_data_dir)
    os.mkdir(dst_logs_dir)
    os.mkdir(dst_fixtures_dir)
    
    create_file(dst_logs_dir, "eoxserver.log")
    
    tags = {
        TAG_PATH_SRC: src_root_dir,
        TAG_PATH_DST: dst_inst_dir,
        TAG_INSTANCE_ID: instance_id
    }

    if args.mapscript_dir:
        tags[TAG_MAPSCRIPT] = args.mapscript_dir

    # copy the template settings file and replace its tags
    copy_and_replace_tags(os.path.join(src_conf_dir, "TEMPLATE_settings.py"),
                          os.path.join(dst_inst_dir, "settings.py"),
                          tags)

    # copy the template config file and replace its tags
    copy_and_replace_tags(os.path.join(src_conf_dir, "TEMPLATE_eoxserver.conf"),
                          os.path.join(dst_conf_dir, "eoxserver.conf"),
                          tags)

    shutil.copy(os.path.join(src_conf_dir, "TEMPLATE_template.map"),
                os.path.join(dst_conf_dir, "template.map"))

    if args.initial_data:
        if os.path.splitext(args.initial_data)[1].lower() != ".json":
            raise Exception("Initial data must be a JSON file.")
        shutil.copy(initial_data, os.path.join(dst_fixtures_dir,
                                               "initial_data.json"))
    
    # initialize the spatialite database file
    if args.init_spatialite:
        print("Setting up initial database.")
        os.chdir(dst_data_dir)
        init_sql = os.path.join(src_conf_dir, "init_spatialite-2.3.sql")
        os.system("spatialite conf.sqlite < %s" % init_sql)

if __name__ == "__main__":
    run(sys.argv[1:])
