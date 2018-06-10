#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import errno
import subprocess
import os
import argparse
from subprocess import call


#
#	Use:
#	1 - Open cmd window in base directory:
#		* SHIFT-RightCLICK at the subject directory name in Explorer
#		* select 'Open cmd-window here'
#	2 - type: 'doPandoc --help' to get a full overview of its use
#
#
#	Include:
#		templates\<arg3>.[docx | tex]		(optional) the Word or Tex templates to be used by pandoc
#		src\mmd\<arg1>.mmd						This is the actual source mmd file
#		src\bib\<bibliography.bib>				(optional) your bib file, overrides as specified in the YAML-block
#		src\images							Here are the images stored that are used in the document
#		results\							This is directory where the generated result will be placed
#
#	Result: results\<arg1>.<arg2>
#


def InputError(msg, expr):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    print('ERROR: ' + msg + ': ' + expr + '\n')
    print('Type \'doPandoc -h\' for help\n')
    exit(1)
    return (0)


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def gitCommit(project=None, msg=None, versionLevel=None):
    # Open shell and
    # * Check for untracked textual assets and stage them
    # * increment version, if relevant.
    #	Note that only incremented versions are transferred as a tag to the source.
    #	Note that the returned version will be inserted into the document, hence maintain the same version if no updates are found.
    # * commit changes
    # * push to remote
    assert project
    assert msg
    try:
        scrivdir = project + '.scriv/Files/Docs/*.rtf'
        result = subprocess.run(args=['git', 'add', scrivdir], stdout=subprocess.PIPE, stderr=None, shell=True,
                                check=True)
        result = subprocess.run(args=['git', 'add', '-u'], stdout=subprocess.PIPE, stderr=None, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("git staging error: {}".format(result.stderr))
        return ''
    # Commit, use commit message
    try:
        result = subprocess.run(args=['git', 'commit', '-m"' + msg + '"'], stdin=None, input=None,
                                stdout=subprocess.PIPE, stderr=None, shell=True, timeout=None, check=True)
        # Push the local git commits to the remote repository
        result = subprocess.run(args=['git', 'push', '--follow-tags'], stdout=subprocess.PIPE, stderr=None, shell=True,
                                check=True)

        # Automagically increment the version number, depending on requested level
        # - None(default): just commit, with new total commits identifying this change
        # - Minor: increment minor version level
        # - Major: increment major version level
        if versionLevel in ['minor', 'major']:
            version = gitIncrementVersion(versionLevel)
        elif versionLevel != None:
            print(
                'Incorrect versioning request: can only support "None" (default), "minor" or "major", got "{}"'.format(
                    versionLevel))
        else:
            version = getVersion(True)
    except subprocess.CalledProcessError:
        # Push or commit returned error: Probably there are no changes to commit, hence return current version
        version = getVersion(True)
        print("git commit/push error ({}) - maintaining current version ({}).".format(result.stderr, version))
    return version


def getVersion(concat=False):
    root = subprocess.check_output(['git', 'describe', '--long']).decode(
        'ascii').rstrip()  # Establish tag (=version), hash and commits on top of current version
    tag, commits, hash = root.split('-')
    major, minor = tag[1:].split('.')
    if concat:
        return tag + '-' + commits
    else:
        return int(major), int(minor), commits


def gitIncrementVersion(level=None):
    # Open shell and Increment the current git number
    major, minor, commits = getVersion()
    if level == 'minor':
        minor += 1
        commits = 0
    elif level == 'major':
        major += 1
        minor = 0
        commits = 0
    else:
        print("gitIncrementVersion error: Cannot process {}".format(result.stderr))
    tag = 'v' + str(major) + '.' + str(minor)
    tagMsg = 'Version ' + tag
    try:
        result = subprocess.run(args=['git', 'tag', '-a', tag, '-m "' + tagMsg + '"'], stdin=None, input=None,
                                stdout=subprocess.PIPE, stderr=None, shell=True, timeout=None, check=True)
    except subprocess.CalledProcessError:
        print("git tagging error: {}".format(result.stderr))
    return tag + '-' + str(commits)


# debug: PRINT ARGUMENTS
# print ('arguments (', len(sys.argv), ') to this cmd are:: \n')
# print (str(sys.argv), flush=True)

# Set default template extensions for the various pandoc target formats
default = {}
default['docx'] = '.docx'
default['doc'] = '.doc'
default['tex'] = '.tex'
default['pdf'] = '.tex'
default['md'] = '.mmd'
default['mmd'] = '.mmd'
default['-d'] = 'templates'
default['-l'] = None
default['-t'] = 'pandoc-docstyle'
default['-s'] = 'src'
default['-r'] = 'results'
default['-p'] = 'DissertatieBrandt'

# Configure which pandoc extensions to include in the command
pandocExts = 'markdown_mmd'
pandocExts = pandocExts + '+auto_identifiers'
pandocExts = pandocExts + '+implicit_header_references'
pandocExts = pandocExts + '+yaml_metadata_block'
pandocExts = pandocExts + '+citations'
pandocExts = pandocExts + '+implicit_figures'
pandocExts = pandocExts + '+header_attributes'
pandocExts = pandocExts + '+pipe_tables'
pandocExts = pandocExts + '+grid_tables'
pandocExts = pandocExts + '+multiline_tables'
pandocExts = pandocExts + '+table_captions'
pandocExts = pandocExts + '+strikeout'
pandocExts = pandocExts + '+footnotes'
pandocExts = pandocExts + '+inline_notes'
pandocExts = pandocExts + '+tex_math_dollars'
pandocExts = pandocExts + '+superscript'
pandocExts = pandocExts + '+subscript'
pandocExts = pandocExts + '+raw_tex'
pandocExts = pandocExts + '+definition_lists'
pandocExts = pandocExts + '+fancy_lists'
pandocExts = pandocExts + '+example_lists'
pandocExts = pandocExts + '+startnum'
pandocExts = pandocExts + '+fenced_code_blocks'
pandocExts = pandocExts + '+fenced_code_attributes'
pandocExts = pandocExts + '+link_attributes'

# Get all arguments and ACK the command
parser = argparse.ArgumentParser(
    description='Wrapper around pandoc to spare lotsa typing!',
    epilog='''Besides the arguments above, any APPENDED arguments will be transferred 1-to-1 to pandoc, e.g., --toc. \n
            Execute this program by including the location of the program in the environment's PATH variable. \n
			All relative directories are relative to the current working directory of the shell.\n
            Make sure you include templates\ and src\ directories in the working directory.
			You can change these defaults by applying appropriate options.\n
            Regarding the expected structure of the project:
			* templates\ contains the template files to be used by pandoc, \n
            * src\ contains:\n
				- docs\ for your primary document source files (mmd or tex or docx or whatever), \n
				- bib\ for bib sources, \n
				- images\ for images used in your document. \n
            * results\ contains rhe result of the pandoc processing as: <source>.<format>\n
    '''
)
parser.add_argument('source', help='the name of the source file; leaving out the extension assumes .mmd')
parser.add_argument('format', choices=['doc', 'docx', 'tex', 'pdf'], help='the target format: [doc | docx | tex | pdf]')
parser.add_argument('-g', '--git',
                    help='(optional) use git-versioning to commit the current text, tagged as new minor version. The text following this argument is considered the commit message (try to scale it to 50 chars). Only useful when you checked out your scrivener project from git',
                    default=None)
parser.add_argument('-l', '--level', choices=['minor', 'major', 'none'],
                    help='(optional) the version level that will be incremented (requires option -g <msg>, unless "-l none")',
                    default=default['-l'])
parser.add_argument('-t', '--template',
                    help='(optional) your style template file; leaving out the extension implies compatibility with specified target format ',
                    default=default['-t'])
parser.add_argument('-d', '--dDir',
                    help='(optional) the root directory (relative to your project dir) holding the style template file ',
                    default=default['-d'])
parser.add_argument('-s', '--sDir', help='(optional) the root directory (relative) holding the source document files ',
                    default=default['-s'])
parser.add_argument('-r', '--rDir',
                    help='(optional) the results directory (relative) holding the generated target file ',
                    default=default['-r'])
parser.add_argument('-b', '--bib',
                    help='(optional) your bib file, overriding what has been specified in the YAML-block; leaving out the extension assumes .bib')
parser.add_argument('-p', '--proj',
                    help='(optional) the scrivener project(.scriv) directory holding the scrivener sources; assumes {} '.format(
                        default['-p']), default=default['-p'])
args = parser.parse_known_args()

source = args[0].source
path, srcfile = os.path.split(source)
root, ext = os.path.splitext(srcfile)
if not ext:
    ext = '.mmd'
sourceFile = root + ext

gitMessage = args[0].git
targetDir = args[0].rDir
format = args[0].format
templateDir = args[0].dDir
project = args[0].proj
if path == os.path.join(args[0].sDir, "docs"):
    sourceDir = args[0].sDir
else:
    sourceDir = os.path.join(path, args[0].sDir)
baseDir = os.getcwd()  # The shell's current working directory
mmdDir = os.path.join(sourceDir, "docs")
bibDir = os.path.join(sourceDir, "bib")
imgDir = os.path.join(sourceDir, "images")

root, ext = os.path.splitext(args[0].template)
if not ext:
    ext = default[args[0].format]
templateFile = root + ext

if args[0].bib:  # If it's not defined here, YAML-block data is assumed
    root, ext = os.path.splitext(args[0].bib)
    print('head: <' + root + '>, tail: <' + ext + '>')
    if not ext:
        ext = '.bib'
    bibFile = root + ext

targetFile = os.path.splitext(sourceFile)[0] + '.' + format

# Consider the use of versioning. Note that the options  '-l' and '-g' are related
version = ''
if args[0].level and args[0].level in ['major', 'minor']:
    assert gitMessage and len(
        gitMessage) > 1, "Will not create a new version without a proper commit message; '-l' demands '-g <msg>'"
    version = gitCommit(project=project, msg=gitMessage, versionLevel=args[0].level)
elif gitMessage:
    assert len(
        gitMessage) > 1, "Will not commit without a proper commit message; either use '-g <msg>' or don't use '-g'"
    # Since a git message is present, increment the minor version
    version = gitCommit(project=project, msg=gitMessage, versionLevel='minor')
elif args[0].level == 'none':
    version = None
else:
    # Commit the current status, but maintain the current version. This commit is distinguishable by its increment of the total commits only
    version = gitCommit(project=project, msg='(auto message) Small textual changes only')

if version == '':
    version = getVersion(True)
# root = subprocess.check_output(['git', 'describe']).decode('ascii').rstrip()	# Establish tag (=version), hash and commits on top of current version
# tag, commits, hash = root.split('-')
# version = tag + '-' + commits  # + '-t' + totalcommits

print('base directory is    :' + baseDir)
print('template directory is:' + templateDir)
print('source file is       :' + sourceFile)
print('target file is       :' + targetFile)
print('template file is     :' + os.path.join(templateDir, templateFile))
print('version is           :' + (version if version else ''))

if not os.path.exists(os.path.join(baseDir, mmdDir, sourceFile)):
    print('source file not found', os.path.join(baseDir, mmdDir, sourceFile))
    print('searching subfolder ...')
    # Especially with scrivener mmd projects, an additional compile folder may be introduced
    if not os.path.exists(os.path.join(baseDir, mmdDir, sourceFile, sourceFile)):
        InputError('source file not found', os.path.join(baseDir, mmdDir, sourceFile, sourceFile))
    else:
        src_filename = os.path.join(mmdDir, sourceFile, sourceFile)
else:
    src_filename = os.path.join(mmdDir, sourceFile)
if not os.path.exists(os.path.join(baseDir, templateDir, templateFile)): InputError('template file not found',
                                                                                    os.path.join(baseDir, templateDir,
                                                                                                 templateFile))

# Parse and build the arguments for pandoc

pandoc_args = {}
pandoc_args['-f'] = pandocExts
pandoc_args['-o'] = os.path.join(targetDir, targetFile)
print('output to            :' + pandoc_args['-o'])
pandoc_args['--data-dir'] = baseDir
pandoc_args[
    '--filter'] = 'pandoc-citeproc'  # Using an external filter, pandoc-citeproc, pandoc can automatically generate citations and a bibliography in a number of styles
if args[0].bib:  # Bibliography file given as argument that overrides YAML block
    pandoc_args['--bibliography'] = os.path.join(bibDir, bibFile)
pandoc_bools = [
    "--number-sections"]  # ".. as seen in section 2.1.3" You can configure (1) which symbol to use (num-sign by default), and (2) whether to link back to the referred section, or convert the link to plain text (link by default)
pandoc_bools.append("--chapters")  # Treat mmd top-level headers as chapters
pandoc_bools.append(
    "--smart")  # Produce typographically correct output, converting straight quotes to curly quotes, --- to em-dashes, -- to en-dashes, and ... to ellipses, etc.
if version:
    pandoc_args[
        '-M'] = 'version=' + version  # Pass the version for this document as meta-data to be used in the template
if (format == "docx"):
    pandoc_args['--reference-docx'] = os.path.join(templateDir, templateFile)
else:
    pandoc_args['--template'] = os.path.join(templateDir, templateFile)

pArgs = ['pandoc']
for key in ('-o', '-f'):
    pArgs.extend([key, pandoc_args[key]])
    del pandoc_args[key]

for key, val in pandoc_args.items():
    pArgs.extend([key, val])

pArgs.extend(pandoc_bools)

# Add non-parsed, additional arguments from the command line, if any
for val in args[1]:
    pArgs.append(val)

# Append the mmd source
pArgs.append(src_filename)

with cd(baseDir):
    print('changed dir to: ' + os.getcwd())
    print('About to run \n', pArgs)

    rc = subprocess.call(pArgs)  # Do the actual pandoc operation and safe its return value

    if (rc == 0):  # When pandoc didn't complain, open the resulting file
        os.startfile(os.path.join(targetDir, targetFile), 'open')
    else:
        print("\n\n>>>> ERROR: pandoc returned with {}".format(rc))

print('Done!\n')



