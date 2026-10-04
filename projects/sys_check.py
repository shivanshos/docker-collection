#!/usr/bin/env python3
import psutil

memory = psutil.virtual_memory()
print(f'Memory usage: {memory.percent}%')