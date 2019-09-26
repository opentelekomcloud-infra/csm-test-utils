# Customer Service Monitoring test utils

This repository contains set of simple Go-based utils for testing of CSM-created infrasctucture

### Why use Go for tests?

 - There are tests written in *Python* inside of [csm-sandbox](https://github.com/opentelekomcloud-infra/csm-sandbox) itself.
But in some cases *go* works several times faster and code seems to be simplier.

 - Already built test app doesn't have any requirements, *Python* for tests leads to increasing number of used libraries.
 
 - Doesn't depend on Python version

 - It's fun

**We use already built test scripts for [csm-sandbox](https://github.com/opentelekomcloud-infra/csm-sandbox),
Go on client is not required**

*Language by default to be used for tests is still Python 3.6+*

### Usage

This repo to contain multiple tests

#### Load Balancer Test
Usage:

`load_balancer_test <remote_ip> [request count]`

e.g.

`load_balancer_test 80.158.33.113 1000`
