from signalsmanagerImp import *


class ISignalsManagerActionConnect(SignalsManagerActionConnectImp):
    """Summary

    Returns:
        TYPE: Description
    """

    def connect(self, qobject, signal_signature):
        """Summary
        Args:
            qobject (TYPE): Description
            signal_signature (TYPE): Description
        Returns:
            TYPE: Description
        """
        return self._connect_with_key_test_(
            self._build_key_(qobject, signal_signature)
        )

    def connect_all(self):
        """Summary
        Returns:
            TYPE: Description
        """
        self._action_for_all_(
            {
                'action_for_all': self._connect_with_key_test_
            }
        )

    def connect_group(self, s_group="all"):
        """Summary
        Args:
            s_group (str, optional): Description
        Returns:
            TYPE: Description
        """
        return self._action_for_group_with_test_(
            {
                'action_for_all': self.connect_all,
                'action_with_key_test': self._connect_with_key_test_,
                's_group': s_group
            }
        )


class ISignalsManagerActionDisconnect(SignalsManagerActionDisconnectImp):
    """Summary
    
    Returns:
        TYPE: Description
    """

    def disconnect(self, qobject, signal_signature):
        """Summary
        Args:
            qobject (TYPE): Description
            signal_signature (TYPE): Description
        Returns:
            TYPE: Description
        """
        return self._disconnect_with_key_test_(
            self._build_key_(qobject, signal_signature)
        )

    def disconnect_all(self):
        """Summary
        Returns:
            TYPE: Description
        """
        self._action_for_all_(
            {
                'action_for_all': self._disconnect_with_key_test_
            }
        )

    def disconnect_group(self, s_group="all"):
        """Summary
        Args:
            s_group (str, optional): Description
        Returns:
            TYPE: Description
        """
        return self._action_for_group_with_test_(
            {
                'action_for_all': self.disconnect_all,
                'action_with_key_test': self._disconnect_with_key_test_,
                's_group': s_group
            }
        )


class ISignalsManagerActionStart(SignalsManagerActionStartImp):
    """Summary
    
    Returns:
        TYPE: Description
    """

    def start(self, qobject, interval=0.0):
        """Summary
        Args:
            qobject (TYPE): Description
            interval (float, optional): Description
        Returns:
            TYPE: Description
        """
        return self._start_with_key_(
            self._build_key_(qobject, 'timeout ()'), interval
        )

    def start_all(self, interval=0.0):
        """Summary
        Args:
            interval (float, optional): Description
        Returns:
            TYPE: Description
        """
        self._action_for_all_(
            {
                'action_for_all': self._start_with_key_,
                'interval': interval
            }
        )

    def start_group(self, interval=0.0, s_group="all"):
        """Summary
        Args:
            interval (float, optional): Description
            s_group (str, optional): Description
        Returns:
            TYPE: Description
        """
        return self._action_for_group_with_test_(
            {
                'action_for_all': self.start_all,
                'action_with_key_test': self.start_with_key_test,
                's_group': s_group,
                'interval': interval
            }
        )


class ISignalsManagerActionStop(SignalsManagerActionStopImp):
    """Summary
    
    Returns:
        TYPE: Description
    """

    def stop(self, qobject):
        """Summary
        Args:
            qobject (TYPE): Description
        Returns:
            TYPE: Description
        """
        return self._stop_with_key_test_(
            self._build_key_(qobject, 'timeout ()')
        )

    def stop_all(self):
        """Summary
        Returns:
            TYPE: Description
        """
        self._action_for_all_(
            {
                'action_for_all': self._stop_with_key_test_
            }
        )

    def stop_group(self, s_group="all"):
        """Summary
        Args:
            s_group (str, optional): Description
        Returns:
            TYPE: Description
        """
        return self._action_for_group_with_test_(
            {
                'action_for_all': self.stop_all,
                'action_with_key_test': self._stop_with_key_test_,
                's_group': s_group
            }
        )
