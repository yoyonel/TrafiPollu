"""Summary

Returns:
    TYPE: Description
"""

from trafipolluImp import TrafiPolluImp


class ITrafiPollu(TrafiPolluImp):
    """"""

    def __init__(self, iface, dlg):
        """
        Args:
            iface (TYPE): Description
            dlg (TYPE): Description
        """
        super(ITrafiPollu, self).__init__(iface, dlg)

    def init(self):
        self._init_signals_()

    def update(self):
        pass

    def enable(self):
        self._enable_trafipollu_()

    def disable(self):
        self._disable_trafipollu_()

    def get_dlg(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.dlg


TrafiPollu = ITrafiPollu
