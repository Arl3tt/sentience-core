#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for timestamp formatting and pretty printing
"""
import json
import time

def now_ts():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def pretty(obj):
    try:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    except Exception:
        print(obj)