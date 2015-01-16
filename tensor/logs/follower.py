import os

class LogFollower(object):
    """Provides a class for following log files between runs

    **Arguments:**

    :logfile: Full path to logfile

    **Keyword arguments:**

    :parser: Optional parser method for log lines
    """

    def __init__(self, logfile, parser=None):
        self.logfile = logfile
        self.tmp = '/var/lib/tensor/%s.lf' % self.logfile.lstrip('/').replace('/','-')

        self.readLast()

        self.parser = parser

    def cleanStore(self):
        os.unlink(self.tmp)

    def storeLast(self):
        fi = open(self.tmp, 'wt')
        fi.write('%s:%s' % (self.lastSize, self.lastInode))
        fi.close()

    def readLast(self):
        if os.path.exists(self.tmp):
            fi = open(self.tmp, 'rt')
            ls, li = fi.read().split(':')
            self.lastSize = int(ls)
            self.lastInode = int(li)
        else:
            self.lastSize = 0
            self.lastInode = 0

    def get_fn(self, fn, max_lines=None):
        """Passes each parsed log line to `fn`
        This is a better idea than storing a giant log file in memory
        """
        stat = os.stat(self.logfile)

        if (stat.st_ino == self.lastInode) and (stat.st_size == self.lastSize):
            # Nothing new
            return []

        # Handle rollover and rotations vaguely
        if (stat.st_ino != self.lastInode) or (stat.st_size < self.lastSize):
            self.lastSize = 0

        fi = open(self.logfile, 'rt')
        fi.seek(self.lastSize)

        self.lastInode = stat.st_ino

        lines = 0

        for i in fi:
            lines += 1
            if max_lines and (lines > max_lines):
                self.storeLast()
                fi.close()
                return 

            if '\n' in i:
                self.lastSize += len(i)
                if self.parser:
                    line = self.parser(i.strip('\n'))
                else:
                    line = i.strip('\n')

                fn(line)

        self.storeLast()

        fi.close()

    def get(self, max_lines=None):
        """Returns a big list of all log lines since the last run
        """
        rows = []

        self.get_fn(lambda row: rows.append(row), max_lines=max_lines)

        return rows