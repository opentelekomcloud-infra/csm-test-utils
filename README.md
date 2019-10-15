# Customer Service Monitoring test utils

[![PyPI version](https://img.shields.io/pypi/v/csm-test-utils.svg)](https://pypi.org/project/csm-test-utils/)
[![PyPI license](https://img.shields.io/pypi/l/csm-test-utils.svg)](https://pypi.org/project/csm-test-utils/)

This repository contains set of simple Go- and Python-based utils for testing of CSM-created infrasctucture

### Why use Go for tests?

 - Some times *go* works several times faster and code seems to be simplier.

 - Already built test app doesn't have any requirements, *Python* for tests leads to increasing number of used libraries.
 
 - Doesn't depend on Python version

 - It's fun

### Why use Python for tests?
 - Simple
 - No need to compile 

*Language by default to be used for tests is Python 3.7+*

### Usage

This repo to contain multiple tests

#### Load Balancer Test
Usage:

`load_balancer_test <remote_ip> [request count]`

e.g.

`load_balancer_test 80.158.33.113 1000`
