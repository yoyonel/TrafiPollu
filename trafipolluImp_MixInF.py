__author__ = 'latty'

# url: https://github.com/brentpayne/learning-python/blob/master/MixInMultipleInheritance/mixin_multiple_inheritance.py
class MixInF(object):
    def __init__(self, *args, **kwargs):
        pass

    def transfer_arguments(self, list_args, **kwargs):
        """

        :param list_args:
        :return:

        """
        for id_arg in list_args:
            self.__dict__[id_arg] = kwargs[id_arg]

    @staticmethod
    def update_pyxb_node(node, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # print 'update_pyxb_node - kwargs: ', kwargs
        for k, v in kwargs.iteritems():
            node._setAttribute(k, v)