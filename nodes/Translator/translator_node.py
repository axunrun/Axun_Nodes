class TranslatorNode:
    """
    这是一个空节点类，用于正确注册插件。
    虽然不提供实际的节点功能，但需要它来使插件正确加载。
    """
    CATEGORY = "Translator"
    RETURN_TYPES = ()
    FUNCTION = "run"
    OUTPUT_NODE = True

    def run(self):
        return {} 