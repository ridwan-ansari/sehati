import traceback
from loguru import logger
from contextlib import contextmanager
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.src.utils.response import ResponseContext
from app.src.utils.execeptions import UnauthorizedException, ForbiddenException


@contextmanager
def response_handler():
    response_context = ResponseContext()
    try:
        yield response_context
    except ValueError as error:
        logger.error(str(error))
        response_context.update(False, status.HTTP_400_BAD_REQUEST, str(error))
    except IntegrityError as error:
        logger.error(str(error))
        original_error = error.__dict__.get('orig', error)
        response_context.update(False, status.HTTP_400_BAD_REQUEST, str(original_error))
    except FileNotFoundError as error:
        logger.error(str(error))
        message = str(error) if str(error) else "Resource not found. Ensure you have the correct permissions and that your request parameters are accurate."
        response_context.update(False, status.HTTP_404_NOT_FOUND, message)
    except HTTPException as exc:
        response_context.update(False, exc.status_code, exc.detail)
    except UnauthorizedException as exc:
        response_context.update(False, exc.status_code, exc.detail)
    except ForbiddenException as exc:
        response_context.update(False, exc.status_code, exc.detail)
    except Exception as error:
        traceback.print_exc()
        logger.warning(traceback.format_exc())
        response_context.update(False, status.HTTP_500_INTERNAL_SERVER_ERROR, str(error))