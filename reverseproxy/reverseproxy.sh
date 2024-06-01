#!/bin/bash

mitmdump --listen-host localhost --listen-port 5000 -s reverseproxy.py -v
