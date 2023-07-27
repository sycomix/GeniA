import logging

import openai
from openai.error import APIError, Timeout, TryAgain, APIConnectionError
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from genia.settings_loader import settings

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((Timeout, TryAgain, APIError, APIConnectionError)),
)
def call_model(messages, model=None):
    try:
        logger.debug("calling the model")
        response = openai.ChatCompletion.create(
            temperature=settings["openai"]["temperature"],
            model=model if model is not None else settings["openai"]["OPENAI_MODEL"],
            messages=messages,
            request_timeout=settings["openai"]["timeout"],
        )
        logger.debug("Tokens usage recorded by open AI %s", response["usage"]["total_tokens"])
        return response["choices"][0]["message"]
    except Exception as e:
        logger.error("call model error %s", str(e))
        raise e
