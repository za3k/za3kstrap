import helpers
import re

class DirConfig():
    # Note: In theory 'classify' is a DFA execution
    def __init__(self, lines):
        self.lines = lines
    def specificity(self, pattern):
        return pattern.count("/")*1001 - pattern.count("*")
    def ismatch(self, pattern, path):
        regex = pattern.replace("*", "[^/]+")
        res = re.compile(regex).match(path)
        #print(repr(pattern), repr(regex), path, res, self.specificity(pattern))
        return res
    def classify(self, relpath):
        path = "/" + relpath
        ret = max(
            filter(
                lambda x: self.ismatch(x[1], path),
                self.lines
            ),
            key=lambda x: self.specificity(x[1]),
            default=("e", "default"),
        )
        #print(path, ret, self.lines)
        
        #import sys; sys.exit(0)
        return ret[0]

def read_config(config_file=None):
    parts = helpers.get_dir_file(config_file)
    return DirConfig(parts)
