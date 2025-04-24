import logging

  # Debugging the code:
formatter = logging.Formatter('%(asctime)s[%(name)s] %(levelname)s: %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
openai_logger = logging.getLogger("openai._base_client")
openai_logger.addHandler(handler)
logger = logging.getLogger('volvo_bot')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)