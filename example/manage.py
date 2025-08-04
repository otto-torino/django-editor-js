#!/usr/bin/env python
import os
import sys
import dotenv

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
