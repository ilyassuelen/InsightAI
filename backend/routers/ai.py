import os
from dotenv import load_dotenv
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
from openai import OpenAI

router = APIRouter()
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic model for request body
class PromptRequest(BaseModel):
    prompt: str


@router.post("/")
def generate_text(request: PromptRequest):
    """
    Generates a text using OpenAI API.
    Handles possible OpenAI exceptions and returns appropriate HTTP responses.
    """
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=request.prompt
        )

        return {"response": response.output_text}

    except openai.PermissionDeniedError:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Access denied for the requested model or API key."}
        )
    except openai.RateLimitError as e:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": f"OpenAI API request exceeded rate limit: {e}"}
        )
    except openai.APIConnectionError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": f"Failed to connect to OpenAI API: {e}"}
        )
    except openai.BadRequestError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid request: {e}"}
        )
    except openai.APIError as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"OpenAI API returned an API Error: {e}"}
        )
