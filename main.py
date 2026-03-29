import sys

from simple_analysis import main as simple_main
from advanced_analysis import main as advanced_main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "advanced":
        advanced_main()
    else:
        simple_main()