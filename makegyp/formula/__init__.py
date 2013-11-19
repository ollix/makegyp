class Formula(object):
    url = None
    sha1 = None

    def install(self):
        print 'installing %s...' % self.__class__.__name__
        self.make()

    def make(self):
        pass
