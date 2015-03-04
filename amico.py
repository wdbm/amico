#!/usr/bin/env python

"""
################################################################################
#                                                                              #
# amico                                                                        #
#                                                                              #
################################################################################
#                                                                              #
# LICENCE INFORMATION                                                          #
#                                                                              #
# This program interfaces with the ATLAS Metadata Interface and compares       #
# dataset metadata such that results above a certain match quality are         #
# collated.                                                                    #
#                                                                              #
# 2015 Will Breaden Madden, w.bm@cern.ch                                       #
#                                                                              #
# Subject to ATLAS Data Access Policy, this software is released under the     #
# terms of the GNU General Public License version 3 (GPLv3).                   #
#                                                                              #
# For a copy of the ATLAS Data Access Policy, see                              #
# DOI: 10.7483/OPENDATA.ATLAS.T9YR.Y7MZ or http://opendata.cern.ch/record/413. #
#                                                                              #
# For a copy of the GNU General Public License, see                            #
# http://www.gnu.org/licenses/.                                                #
#                                                                              #
################################################################################

Usage:
    program [options]

Options:
    -h, --help                 display help message
    --version                  display version and exit
    -v, --verbose              verbose logging
    -u, --username=USERNAME    username
    --pattern1=PATTERN         AMI search pattern [default: %mc14_13TeV%]
    --pattern2=PATTERN         AMI search pattern [default: %8TeV%]
    --percentage=NUMBER        percentage match [default: 40]
    --maxresults=NUMBER        maximum number of AMI results [default: 10]
"""

name    = "amico"
version = "2015-03-04T2245Z"
logo    =\
"""                    _           
   ____ _____ ___  (_)________  
  / __ `/ __ `__ \/ / ___/ __ \ 
 / /_/ / / / / / / / /__/ /_/ / 
 \__,_/_/ /_/ /_/_/\___/\____/  """

def smuggle(
    moduleName = None,
    URL        = None
    ):
    if moduleName is None:
        moduleName = URL
    try:
        module = __import__(moduleName)
        return(module)
    except:
        try:
            moduleString = urllib.urlopen(URL).read()
            module = imp.new_module("module")
            exec moduleString in module.__dict__
            return(module)
        except: 
            raise(
                Exception(
                    "module {moduleName} import error".format(
                        moduleName = moduleName
                    )
                )
            )
            sys.exit()

import os
import logging
from collections import *
import urllib
import imp
import pyAMI
import pyAMI.client
import pyAMI.atlas.api
docopt = smuggle(
    moduleName = "docopt",
    URL = "https://rawgit.com/docopt/docopt/master/docopt.py"
)
technicolor = smuggle(
    moduleName = "technicolor",
    URL = "https://rawgit.com/wdbm/technicolor/master/technicolor.py"
)
shijian = smuggle(
    moduleName = "shijian",
    URL = "https://rawgit.com/wdbm/shijian/master/shijian.py"
)
pyprel = smuggle(
    moduleName = "pyprel",
    URL = "https://rawgit.com/wdbm/pyprel/master/pyprel.py"
)

@shijian.timer
def main(options):

    global program
    program = Program(options = options)

    pattern1               = options["--pattern1"]
    pattern2               = options["--pattern2"]
    percentage             = options["--percentage"]
    maximumNumberOfResults = int(options["--maxresults"])

    pyAMI_auditor()
    client = pyAMI.client.Client('atlas')
    pyAMI.atlas.api.init()

    log.info("\nquery AMI for patterns\n\n- {pattern1}\n- {pattern2}\n".format(
        pattern1 = pattern1,
        pattern2 = pattern2
    ))
    log.info("limit on number of results: {maximumNumberOfResults}".format(
        maximumNumberOfResults = maximumNumberOfResults
    ))

    datasets1 = pyAMI.atlas.api.list_datasets(
        client,
        patterns = [pattern1],
        fields = [
            "ldn",
            "physics_short"
        ],
        limit = [1, maximumNumberOfResults],
        type = "AOD"
    )

    datasets2 = pyAMI.atlas.api.list_datasets(
        client,
        patterns = [pattern2],
        fields = [
            "ldn",
            "physics_short"
        ],
        limit = [1, maximumNumberOfResults],
        type = "AOD"
    )

    matches = matches_by_short_physics(
        datasets1  = datasets1,
        datasets2  = datasets2,
        percentage = percentage
    )

    log.info("")

    # Display datasets1 table.
    datasets1TableContents = [[
        "dataset number",
        "short description"
    ]]
    for dataset in datasets1:
        datasets1TableContents.append([
            dataset["ldn"],
            dataset["physics_short"],
        ])
    log.info("datasets of pattern {pattern}:\n".format(pattern = pattern1))
    log.info(pyprel.Table(contents = datasets1TableContents))

    # Display datasets2 table.
    datasets2TableContents = [[
        "dataset number",
        "short description"
    ]]
    for dataset in datasets2:
        datasets2TableContents.append([
            dataset["ldn"],
            dataset["physics_short"],
        ])
    log.info("datasets of pattern {pattern}:\n".format(pattern = pattern2))
    log.info(pyprel.Table(contents = datasets2TableContents))

    # Display matches table.
    matchesTableContents = [[
        "dataset number",
        "short description",
        "dataset number",
        "short description"
    ]]
    for match in matches:
        matchesTableContents.append([
            match[0]["ldn"],
            match[0]["physics_short"],
            match[1]["ldn"],
            match[1]["physics_short"]
        ])
    log.info("datasets matched with {percentage}% match parameter:\n".format(
        percentage = percentage
    ))
    if matches:
        log.info(pyprel.Table(contents = matchesTableContents))
    else:
        log.info("no matches\n".format(pattern = pattern1))

    program.terminate()

class Program(object):

    def __init__(
        self,
        parent  = None,
        options = None
        ):

        # internal options
        self.displayLogo           = True

        # clock
        global clock
        clock = shijian.Clock(name = "program run time")

        # name, version, logo
        if "name" in globals():
            self.name              = name
        else:
            self.name              = None
        if "version" in globals():
            self.version           = version
        else:
            self.version           = None
        if "logo" in globals():
            self.logo              = logo
        elif "logo" not in globals() and hasattr(self, "name"):
            self.logo              = pyprel.renderBanner(
                                         text = self.name.upper()
                                     )
        else:
            self.displayLogo       = False
            self.logo              = None

        # options
        self.options               = options
        self.userName              = self.options["--username"]
        self.verbose               = self.options["--verbose"]

        # default values
        if self.userName is None:
            self.userName = os.getenv("USER")

        # logging
        global log
        log = logging.getLogger(__name__)
        logging.root.addHandler(technicolor.ColorisingStreamHandler())

        # logging level
        if self.verbose:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

        self.engage()

    def engage(
        self
        ):
        pyprel.printLine()
        # logo
        if self.displayLogo:
            log.info(pyprel.centerString(text = self.logo))
            pyprel.printLine()
        # engage alert
        if self.name:
            log.info("initiate {name}".format(
                name = self.name
            ))
        # version
        if self.version:
            log.info("version: {version}".format(
                version = self.version
            ))
        log.info("initiation time: {time}".format(
            time = clock.startTime()
        ))

    def terminate(
        self
        ):
        clock.stop()
        log.info("termination time: {time}".format(
            time = clock.stopTime()
        ))
        log.info("time statistics report:\n{report}".format(
            report = shijian.clocks.report()
        ))
        log.info("terminate {name}".format(
            name = self.name
        ))
        pyprel.printLine()

@shijian.timer
def pyAMI_auditor():
    # Access environment.
    ATLAS_LOCAL_PYAMI_VERSION = os.getenv("ATLAS_LOCAL_PYAMI_VERSION")
    PYAMI_HOME = os.getenv("PYAMI_HOME")
    # Ensure pyAMI environment.
    log.debug("ensure existence of pyAMI environment")
    if ATLAS_LOCAL_PYAMI_VERSION == None or PYAMI_HOME == None:
        log.error("pyAMI environment not detected")
        sys.exit()

@shijian.timer
def intersection(
    list1 = None,
    list2 = None
    ):
    """
    Return the intersection elements of two lists of elements.
    """
    # Prevent modification of lists.
    list1 = list1[:]
    list2 = list2[:]
    # If list2 is shorter than list1, iterate through list2, otherwise iterate
    # through list1.
    if len(list2) < len(list1):
        list1, list2 = list2, list1
    intersection = [
        list2.pop(list2.index(element)) for element in list1 if element in list2
    ]
    return(intersection)

@shijian.timer
def similarity(
    string1    = None,
    string2    = None,
    delimiter  = "_"
    ):
    """
    Return the similarity of two strings of delimited elements. The fraction of
    the number of intersection elements compared to the number of elements of
    the string with fewer elements is returned as a percentage. The lower the
    percentage, the weaker the match; the stronger the percentage, the stronger
    the match.
    """
    if len(string2) < len(string1):
        string1, string2 = string2, string1
    string1Elements = string1.split(delimiter)
    string2Elements = string2.split(delimiter)
    intersectionElements = intersection(
        list1 = string1Elements,
        list2 = string2Elements
    )
    percentageMatch =\
        float(100) * len(intersectionElements) / len(string1Elements)
    return(percentageMatch)

@shijian.timer
def matches_by_short_physics(
    datasets1  = None,
    datasets2  = None,
    percentage = 60
    ):
    # Check each dataset of datasets1 against each dataset of results2. If there
    # is a match greater than a certain quality, record the match.
    matches    = []
    for dataset1 in datasets1:
        for dataset2 in datasets2:
            if similarity(
                string1 = dataset1["physics_short"],
                string2 = dataset2["physics_short"]
            ) > percentage:
                matches.append([dataset1, dataset2])
    return(matches)

if __name__ == "__main__":
    options = docopt.docopt(__doc__)
    if options["--version"]:
        print(version)
        exit()
    main(options)
