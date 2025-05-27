from vip_client.utils import vip
import os
import sys
import json
import boutiques
import contextlib
import urllib.parse
import copy
import re
import csv
from pathlib import Path
import argparse

# global flags
init_api_done = False
debug = False

# print message on stderr
def printerr(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)

# print message on stderr and exit
def fatal_error(*args, **kwargs) -> None:
    printerr(*args, **kwargs)
    exit(1)

# get VIP server URL
def get_vip_url() -> str:
    if not "VIP_API_URL" in os.environ:
        fatal_error("VIP_API_URL not set")
    return os.environ["VIP_API_URL"]

# initialize VIP API
def init_api() -> None:
    global init_api_done
    if init_api_done:
        return
    # get API key
    if not "VIP_API_KEY" in os.environ:
        fatal_error("VIP_API_KEY not set")
    vip_apikey = os.environ["VIP_API_KEY"]
    # configure both, in the right order
    vip.set_vip_url(get_vip_url())
    vip.setApiKey(vip_apikey)
    init_api_done = True

# make app object from GET /rest/admin/appVersions response
def convert_app_version(av):
    name = av["applicationName"]
    identifier = name+"/"+av["version"]
    desc = json.loads(av["descriptor"])
    return {"name":name,"identifier":identifier,"descriptor":desc,"rawtext":av["descriptor"],"resources":av["resources"],"tags":av["tags"],"is_visible":av["visible"],"settings":av["settings"]}

# get_apps(): get a list of apps and descriptors from a VIP-portal instance
def get_apps() -> list:
    init_api()
    app_versions = vip.generic_get("admin/appVersions")
    return list(map(convert_app_version, app_versions))

# get_app(): get a single app
def get_app(identifier) -> object:
    init_api()
    try:
        appver = vip.generic_get("admin/appVersions/"+urllib.parse.quote(identifier))
    except RuntimeError as e:
        # XXX this is not a very good way to test whether an app exists or not:
        # something that explicitly searches for and idea and returns true/false
        # with 200 OK would be more reliable.
        # print(e) # Error 8000 from VIP 
        return None
    return convert_app_version(appver)

# normalized descriptor filename, assuming name & version are already ok
def descriptor_filename(appname, appversion):
    filename = appname + "-" + appversion + ".json"
    return filename.replace(" ", "_")

# normalized container image name
def container_image_name(contimg: dict):
    image = contimg["image"]
    if ":" not in image:
        return None
    # tag is mandatory in this context
    img_tag = image.split(":")
    if len(img_tag) != 2:
        return None
    items = img_tag[0].split("/")
    if len(items) < 1:
        return None
    name = items[len(items) - 1]
    tag = img_tag[1]
    return name + "-" + tag

# a picky checker on the "container-image" section of descriptors:
# . avoid useless values for "index"
# . it checks that image names have the form "host.domain/path/repository:tag"
#   where the host/path part is typically "docker.io/library" for dockerhub,
#   a URL to some other registry.
# . a tag must be present and not "latest"
def check_container_image(filepath: str, contimg: dict) -> None:
    # container-image.index
    if "index" in contimg and contimg["index"] != "docker://":
        printerr("warning: %s: suspicious index '%s'" % (filepath, contimg["index"]))
    # container-image.image
    image = contimg["image"]
    # :tag part
    if ":" not in image:
        printerr("warning: %s: image name has no tag" % filepath)
    else:
        img_tag = image.split(":")
        if len(img_tag) != 2:
            printerr("warning: %s: wrong number of ':'" % filepath)
        elif img_tag[1] == "latest":
            printerr("warning: %s: tag 'latest' shouldn't be used" % filepath)
    # host/path items
    items = image.split("/")
    if len(items) < 2 or "." not in items[0]:
        printerr("warning: %s: image name lacks a host part" % filepath) # "docker.io" on dockerhub
    elif len(items) < 3:
        printerr("warning: %s: image name lacks an explicit path" % filepath) # typically "library/" on dockerhub

# load a descriptor from a file, and check its validity
def load_descriptor(filepath, silent=False) -> dict:
    try:
        # just check that we can open the file, to get some cleaner exception
        # than what boutiques.validate() raises on file not found
        with open(filepath, "r") as f:
            pass
        # bosh validate
        # https://boutiques.github.io/doc/_validate.html#python-api
        with open("/dev/null", "w") as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f): # silence boutiques output
            boutiques.validate(str(filepath))
    # boutiques exception is over-verbose when checking a json file that
    # doesn't match its schema: catch the relevant exception, and show a
    # shorter message.
    # Also note that ValueError is raised by our own checks,
    # and also a parent of simplejson.errors.JSONDecodeError in boutiques
    except (ValueError,boutiques.DescriptorValidationError) as e:
        if type(e) == boutiques.DescriptorValidationError:
            raise ValueError("bosh validate failed")
        else:
            raise e
    # parse the descriptor again, for our own use
    file = {"path":filepath, "identifier":"", "descriptor":None, "rawtext":None}
    with open(filepath, "r") as f:
        rawtext = f.read()
        f.seek(0)
        desc = json.load(f)
        appname = desc["name"]
        appversion = desc["tool-version"]
        # check name and version strings
        if not re.match(r"^[a-zA-Z0-9_\. +-]+$", appname):
            raise ValueError("invalid name '%s'" % appname)
        if not re.match(r"^[a-zA-Z0-9_\.@ +-]+$", appversion):
            raise ValueError("invalid version '%s'" % appversion)
        # check container-image (just warnings)
        if not silent:
            if not "container-image" in desc:
                printerr("warning: %s: no container-image" % filepath)
            else:
                check_container_image(filepath, desc["container-image"])
        # store a parsed version of the descriptor in "descriptor",
        # and the exact original file content in "rawtext"
        file["identifier"] = appname + "/" + appversion
        file["descriptor"] = desc
        file["rawtext"] = rawtext
    return file

# helper for get_files_*
def add_file(files, filepath, silent=False):
    try:
        file = load_descriptor(filepath, silent=silent)
        identifier = file["identifier"]
        if identifier in files and not silent:
            printerr("ignoring %s: duplicate identifier '%s'"
                     % (filepath, identifier))
            return None
        return file
    # skip invalid files
    except ValueError as e:
        if not silent:
            printerr("ignoring %s: invalid descriptor (%s)" % (filepath, e))
            return None

# get an identifier-indexed dict of valid boutiques descriptors in a directory.
# This uses a flat list of *.json files, no recursive directories walk so far.
def get_files_from_dir(dirname: str, silent=False) -> dict:
    local_path = Path(dirname)
    files = {}
    for f in local_path.iterdir():
        if f.is_file() and f.match("*.json"):
            filepath = local_path.joinpath(f)
            file = add_file(files, filepath, silent=silent)
            if file != None:
                identifier = file["identifier"]
                files[identifier] = file
    return files

# same as above, but from a CSV index
# each app is expected to have three strings: name,version,descriptorPath,
# resolved from the CSV header
def get_files_from_index(indexfile: str, silent=False) -> dict:
    # load csv data
    csv_header = None
    csv_rows = []
    with open(indexfile) as f:
        rows = csv.reader(f, delimiter=',', quotechar='"')
        for row in rows:
            if csv_header == None: # header
                csv_header = {}
                for pos,name in enumerate(row):
                    csv_header[name] = pos
            else: # data
                csv_rows.append(row)
    # check that we have a complete header
    if not (csv_header
            and "name" in csv_header
            and "version" in csv_header
            and "descriptorPath" in csv_header):
        fatal_error("%s: missing fields in header" % indexfile)
    # create files list
    files = {}
    for row in csv_rows:
        filepath = row[csv_header["descriptorPath"]]
        # descriptor path:
        if filepath.startswith("/"): # absolute, use as is
            filepath = Path(filepath)
        else: # relative, resolve from index
            filepath = Path(os.path.join(os.path.dirname(indexfile), filepath))
        # parse descriptor
        file = add_file(files, filepath, silent=silent)
        if file != None:
            # got a valid descriptor file
            identifier = file["identifier"]
            desc = file["descriptor"]
            # check that name and version strings match (fatal)
            appname = row[csv_header["name"]]
            appversion = row[csv_header["version"]]
            if appname != desc["name"] and not silent:
                printerr("%s: app name '%s' doesn't match descriptor '%s'"
                         % (filepath, appname, desc["name"]))
                continue
            if appversion != desc["tool-version"] and not silent:
                printerr("%s: app version '%s' doesn't match descriptor '%s'"
                         % (filepath, appname, desc["tool-version"]))
                continue
            # check for normalized descriptor filename (just a warning)
            normname = descriptor_filename(appname, appversion)
            if os.path.basename(filepath) != normname:
                printerr("warning: %s: incorrect descriptor filename, should be '%s'"
                         % (filepath, normname))
            # add file to list
            files[identifier] = file
    return files

# helper class for the default values of extra fields in apps and appversions
class AppFields:
    # XXX TODO: preserve doi, new "origin" field?
    # XXX somewhat obscure behavior: owner/group/citation are app level,
    # not appversion, and can't be changed on update (see import_file())
    # This should either be ajusted to that all fields can be edited (impacting
    # GET requests), or made more explicit in command-line args.

    # default values for a new app:
    owner = None
    groups = []
    citation = ""
    resources = []
    tags = []
    settings = {}
    is_visible = True
    # app is defined on update only, and contains the existing appversion
    # args is defined everytime, and contains user-provided values
    def __init__(self, app=None, args=None):
        # on update, default to keeping existing values
        if app != None:
            self.is_visible = app["is_visible"]
            self.resources = app["resources"]
            self.tags = app["tags"]
            self.settings = app["settings"]
        # override with args values when defined
        # note an important difference between None and "" here:
        # . None means the arg was not specified, so its value is unchanged
        # . "" means 'set to blank'
        # we only allow a subset of fields in args:
        # . at app level (creation only): owner and groups
        # . at appversion level (creation or update): resource
        if args != None:
            if args.owner != None:
                self.owner = None if args.owner == "" else args.owner
            if args.groups != None:
                self.groups = [] if args.groups == "" else args.groups.split(",")
            if args.resources != None:
                self.resources = [] if args.resources == "" else args.resources.split(",")
            if args.visible != None:
                self.is_visible = args.visible

# import an app from a descriptor file to a VIP-portal instance
# file is assumed already loaded and checked, VIP-portal will re-check anyways
def import_file(file, fields, is_overwrite=False, dry_run=True):
    init_api()
    # create app and appVersion objects for the /rest/admin API
    appname = file["descriptor"]["name"]
    version = file["descriptor"]["tool-version"]
    descriptor = file["rawtext"]
    app = {"name":appname,"applicationGroups":fields.groups,"owner":fields.owner,"citation":fields.citation}
    app_url = "admin/applications/" + urllib.parse.quote(appname)
    appver = {"applicationName":appname,"version":version,"descriptor":descriptor,"visible":fields.is_visible,"resources":fields.resources,"tags":fields.tags,"settings":fields.settings}
    appver_url = "admin/appVersions/" + urllib.parse.quote(appname) + "/" + urllib.parse.quote(version)
    msg = ""
    if is_overwrite:
        msg += " (overwrite)"
    if dry_run:
        msg += " (dry run)"
    # never change app on update: doing so would be arguable if there are
    # several appversions per app, and also it avoids having to fetch app
    # fields on GET (see Appfields())
    can_put_app = not is_overwrite
    print("importing app %s %s%s" % (appname, version, msg))
    if debug:
        print("descriptor string:", descriptor)
    if dry_run:
        if can_put_app:
            print("PUT %s %s" % (app_url, app))
        print("PUT %s %s" % (appver_url, appver))
        return
    if can_put_app:
        r = vip.generic_put(app_url, app)
        if debug:
            print("app updated:", r)
    r = vip.generic_put(appver_url, appver)
    if debug:
        print("appVersion updated:", r)

# recursive ordering of nested list/dict structures
# it transforms any dict into a list of 2-tuples to make lists of dicts sortable
def ordered(obj) -> object:
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

# delete an array key if present and empty
def pop_if_empty(desc, field) -> None:
    if field in desc and type(desc[field]) == list and len(desc[field]) == 0:
        desc.pop(field)

# descriptor "normalization"
# When VIP-portal serializes a parsed Descriptor, it adds empty arrays where
# there were null or missing keys. This is only useful if using an API that
# doesn't preserve the raw descriptor text.
def clean_descriptor(desc: dict) -> dict:
    desc = copy.deepcopy(desc)
    pop_if_empty(desc, "online-platform-urls")
    pop_if_empty(desc, "groups")
    # we don't pop "inputs" as it's mandatory in boutiques
    pop_if_empty(desc, "output-files")
    pop_if_empty(desc, "tests")
    pop_if_empty(desc, "error-codes")
    pop_if_empty(desc, "environment-variables")
    if "container-image" in desc:
        item = desc["container-image"]
        pop_if_empty(item, "container-opts")
    for item in desc["inputs"]:
        pop_if_empty(item, "requires-inputs")
        pop_if_empty(item, "disables-inputs")
        pop_if_empty(item, "value-choices")
    if "output-files" in desc:
        for item in desc["output-files"]:
            pop_if_empty(item, "conditional-path-template")
            pop_if_empty(item, "path-template-stripped-extensions")
            pop_if_empty(item, "file-template")
    return desc

# compare two descriptors
def compare_descriptors(d1, d2) -> bool:
    # use raw text when available (should always be the case with the admin API)
    if "rawtext" in d1 and "rawtext" in d2:
        return d1["rawtext"] == d2["rawtext"]
    # otherwise, normalize, and ignore keys order for comparison
    d1 = d1["descriptor"]
    d2 = d2["descriptor"]
    return ordered(clean_descriptor(d1))==ordered(clean_descriptor(d2))

# import helpers
def import_existing_app(app, file, args=None,
                        show_unchanged=True, is_overwrite=False,
                        dry_run=True, force_update=False):
    identifier = app["identifier"]
    fields = AppFields(app=app, args=args)
    # XXX here we could also compare non-descriptor fields?
    if compare_descriptors(app, file) and not force_update:
        if show_unchanged:
            print("%s: unchanged" % identifier)
    elif not is_overwrite:
        print("%s: changes detected, but overwrite is false" % identifier)
    else: # import with overwrite
        print("%s: changes detected, overwriting" % identifier)
        import_file(file, fields, is_overwrite=True, dry_run=dry_run)

def import_new_app(file, fields, dry_run=True):
        print("%s: new app" % file["identifier"])
        import_file(file, fields, is_overwrite=False, dry_run=dry_run)

# sync a list of descriptors with a list of apps (from a VIP instance)
def perform_sync(args, apps, files):
    # sort both lists, then do one linear pass on them
    # we could also use dicts and the sets of their keys.
    apps.sort(key=lambda app: app["identifier"])
    files.sort(key=lambda file: file["identifier"])
    napps = len(apps)
    nfiles = len(files)
    i = 0
    j = 0
    while i < napps or j < nfiles:
        app = apps[i] if i < napps else None
        file = files[j] if j < nfiles else None
        # if we're not at the end of either list, check if app and file
        # identifiers match:
        # . if they don't, process the first one in sort order, and move on
        # . if they do, compare their descriptors
        if app != None and file != None:
            if app["identifier"] < file["identifier"]:
                file = None
            elif app["identifier"] > file["identifier"]:
                app = None
        if app != None and file != None:
            # app identifiers match: compare descriptors and import if changed
            import_existing_app(app, file, args=args,
                                show_unchanged=args.show_unchanged,
                                is_overwrite=args.overwrite,
                                dry_run=args.dry_run,
                                force_update=args.force_update)
            i += 1
            j += 1
        elif app != None:
            if args.show_orphans:
                print("%s: orphan app with no descriptor" % app["identifier"])
            i += 1
        elif file != None: # import new app
            import_new_app(file, AppFields(args=args), dry_run=args.dry_run)
            j += 1

# helper for list_* commands
def print_app(label: str, identifier: str, desc: dict,
              show_descriptor=False, show_imagename=False):
    print("%s: %s" % (label, identifier))
    # normalized descriptor filename:
    # print("  %s" % descriptor_filename(desc["name"], desc["tool-version"]))
    if show_descriptor:
        print("  descriptor: %s" % desc)
    if show_imagename:
        imagename = None
        if "container-image" in desc:
            imagename = container_image_name(desc["container-image"])
        print("  imagename: %s" % imagename)

# list apps and descriptors on a VIP instance
def cmd_list_apps(args):
    apps = get_apps()
    print("found %d apps on %s:" % (len(apps), get_vip_url()))
    for app in apps:
        print_app(app["name"], app["identifier"], app["descriptor"],
                  show_descriptor=args.show_descriptor,
                  show_imagename=args.show_imagename)

# list apps from a directory of boutiques descriptors
def cmd_list_dir(args):
    descriptors = get_files_from_dir(args.dirname, silent=args.silent)
    print("found %d valid descriptors in %s:" % (len(descriptors), args.dirname))
    for identifier in descriptors:
        file = descriptors[identifier]
        print_app(file["path"].name, identifier, file["descriptor"],
                  show_descriptor=args.show_descriptor,
                  show_imagename=args.show_imagename)

# list apps from a CSV index
def cmd_list_index(args):
    descriptors = get_files_from_index(args.filename, silent=args.silent)
    print("found %d valid descriptors in %s:" % (len(descriptors), args.filename))
    for identifier in descriptors:
        file = descriptors[identifier]
        print_app(file["path"].name, identifier, file["descriptor"],
                  show_descriptor=args.show_descriptor,
                  show_imagename=args.show_imagename)

# import a single descriptor file
def cmd_import_file(args):
    filepath = args.filename
    # load and check descriptor
    file = None
    try:
        file = load_descriptor(filepath, silent=args.silent)
    except ValueError as e:
        fatal_error("%s is not a valid descriptor: %s" % (filepath, e))
    # check if app exists
    appname = file["descriptor"]["name"]
    version = file["descriptor"]["tool-version"]
    app = get_app(file["identifier"])
    if app != None: # app already exists
        import_existing_app(app, file, args=args, show_unchanged=True,
                            is_overwrite=args.overwrite,
                            dry_run=args.dry_run,
                            force_update=args.force_update)
    else: # new app
        import_new_app(file, AppFields(args=args), dry_run=args.dry_run)

# check a single descriptor file
def cmd_check_file(args):
    filepath = args.filename
    try:
        file = load_descriptor(filepath, silent=args.silent)
    except ValueError as e:
        fatal_error("%s is not a valid descriptor: %s" % (filepath, e))
    print("OK")

# sync apps from a directory of boutiques descriptors to a VIP instance
def cmd_sync_dir(args):
    # get apps list from VIP
    apps = get_apps()
    # get files list, converting from dict
    files = get_files_from_dir(args.dirname, silent=args.silent)
    files = list(files.values())
    # sync
    perform_sync(args, apps, files)

# sync apps from a CSV index file to a VIP instance
def cmd_sync_index(args):
    # get apps list from VIP
    apps = get_apps()
    # get files list
    files = get_files_from_index(args.filename, silent=args.silent)
    files = list(files.values())
    # sync
    perform_sync(args, apps, files)

def cmd_show_apps(args):
    print(get_apps())

def cmd_show_files(args):
    print(get_files_from_dir(args.dirname, silent=args.silent))

def cmd_show_index(args):
    print(get_files_from_index(args.filename, silent=args.silent))

def add_subcommand(subparsers, name, func, help=None):
    cmd = subparsers.add_parser(name, help=help)
    cmd.add_argument("--silent", action="store_true", help="no warnings")
    cmd.set_defaults(func=func)
    return cmd

# helper to allow --visible=true/false, with default None
def parse_bool(val):
    if isinstance(val, bool):
        return val
    if val.lower() in ("true", "1"):
        return True
    elif val.lower() in ("false", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("boolean expected")

def add_list_options(cmd):
    cmd.add_argument("--show-descriptor", action="store_true", help="show parsed descriptor content")
    cmd.add_argument("--show-imagename", action="store_true", help="show container image name")

def add_import_options(cmd):
    cmd.add_argument("--dry-run", action="store_true", help="perform no changes, just show what would be done")
    cmd.add_argument("--overwrite", action="store_true", help="overwrite existing apps")
    cmd.add_argument("--force-update", action="store_true", help="force update even if descriptor didn't change")
    cmd.add_argument("--owner", type=str, help="set owner for new apps")
    cmd.add_argument("--groups", type=str, help="set groups for new apps")
    cmd.add_argument("--resources", type=str, help="set resources for new or update apps")
    cmd.add_argument("--visible", type=parse_bool, help="set visibility for new or update apps")

def add_sync_options(cmd):
    add_import_options(cmd)
    cmd.add_argument("--show-orphans", action="store_true", help="show apps in VIP-portal with no descriptor in source")
    cmd.add_argument("--show-unchanged", action="store_true", help="show VIP-portal apps which match their descriptor")

### main
def main():
    helpdetail = (
        "Manage VIP apps descriptors.\n"
        "For commands that communicate with a VIP instance, set:\n"
        "export VIP_API_URL=...  # VIP-portal host URL (without /rest)\n"
        "export VIP_API_KEY=...  # Your API key (admin level required)\n"
        )
    parser = argparse.ArgumentParser(prog="vipapps",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description=helpdetail)
    subparsers = parser.add_subparsers()
    # check_file
    cmd = add_subcommand(subparsers, "check_file", cmd_check_file,
                         help="verify a descriptor file")
    cmd.add_argument("filename")
    # import_file
    cmd = add_subcommand(subparsers, "import_file", cmd_import_file,
                         help="import a descriptor file")
    cmd.add_argument("filename")
    add_import_options(cmd)
    # list_apps
    cmd = add_subcommand(subparsers, "list_apps", cmd_list_apps,
                         help="list appversions on a VIP instance")
    add_list_options(cmd)
    # list_dir
    cmd = add_subcommand(subparsers, "list_dir", cmd_list_dir,
                         help="list descriptors in a directory")
    cmd.add_argument("dirname")
    add_list_options(cmd)
    # list_index
    cmd = add_subcommand(subparsers, "list_index", cmd_list_index,
                         help="list descriptors in a CSV index")
    cmd.add_argument("filename")
    add_list_options(cmd)
    # sync_dir
    cmd = add_subcommand(subparsers, "sync_dir", cmd_sync_dir,
                         help="import descriptors from a directory")
    cmd.add_argument("dirname")
    add_sync_options(cmd)
    # sync_index
    cmd = add_subcommand(subparsers, "sync_index", cmd_sync_index,
                         help="import descriptors from a CSV index")
    cmd.add_argument("filename")
    add_sync_options(cmd)

    # internal/debug subcommands
    if debug:
        cmd = add_subcommand(subparsers, "show_apps", cmd_show_apps,
                             help=argparse.SUPPRESS)
        cmd = add_subcommand(subparsers, "show_files", cmd_show_files,
                             help=argparse.SUPPRESS)
        cmd.add_argument("dirname")
        cmd = add_subcommand(subparsers, "show_index", cmd_show_index,
                             help=argparse.SUPPRESS)
        cmd.add_argument("filename")

    # parse args
    argv = sys.argv
    argv.pop(0)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        exit(1)
    args.func(args)
    exit(0)

### entry point
if __name__ == "__main__":
    main()
