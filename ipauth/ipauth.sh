#!/bin/bash

mitmdump --listen-host localhost --listen-port 6000 -s ipauth.py -v
