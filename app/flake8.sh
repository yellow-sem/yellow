#!/bin/bash

flake8 . | grep -v migrations
