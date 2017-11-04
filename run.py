#!/usr/bin/env python
from app import app

app.run(host="localhost", port=9991, processes=30, debug=False)
