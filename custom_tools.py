import json

import requests
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

# Open the file and load its contents into a dictionary
with open("apis.json", 'r') as json_file:
    data = json.load(json_file)

api_json = data["apis"]


# Tool APICall
class APICall(BaseModel):
    api_name: str = Field(description="API name that indicates which API needs to be called")
    payload: str = Field(description="Payload to be sent in the request body (JSON format)")
    headers: dict = Field(description="Header with token value")


def api_call(api_name: str, payload: str, headers: dict) -> str:
    try:
        # Find the API from the JSON config
        api_data = next((api for api in api_json if api["endpoint"].strip("/") == api_name.strip("/")), None)
        if not api_data:
            return "No API Matched"
        if not headers:
            return "Headers not found"
        # Prepare request
        url = f"{data['base_url']}{api_data['endpoint']}"
        payload_data = json.loads(payload) if payload else {}

        # Make API request
        if api_data["method"] == "GET":
            response = requests.get(url, headers=headers, params=payload_data)
        else:
            response = requests.post(url, headers=headers, json=payload_data)

        # Handle response
        if response.status_code in [200, 201]:
            return response.text
        return f"Error {response.status_code}: {response.text}"

    except Exception as e:
        return str(e)


calling = StructuredTool.from_function(
    func=api_call,
    name="calling",
    description="Perform an API call using API details and parameters",
    args_schema=APICall
)


def get_tools():
    return [calling]
