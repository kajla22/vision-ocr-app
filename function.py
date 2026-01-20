import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import os
import time

def main(event: func.EventGridEvent):
    # Get image URL from Event Grid
    image_url = event.get_json()["url"]
    image_name = image_url.split("/")[-1]

    # -----------------------------
    # Connect to Blob Storage
    # -----------------------------
    blob_service_client = BlobServiceClient.from_connection_string(
        os.environ["STORAGE_CONNECTION_STRING"]
    )

    blob_client = blob_service_client.get_blob_client(
        container="images",
        blob=image_name
    )

    local_image_path = f"/tmp/{image_name}"

    # Download image
    with open(local_image_path, "wb") as f:
        f.write(blob_client.download_blob().readall())

    # -----------------------------
    # Connect to Azure Vision OCR
    # -----------------------------
    vision_client = ComputerVisionClient(
        os.environ["VISION_ENDPOINT"],
        CognitiveServicesCredentials(os.environ["VISION_KEY"])
    )

    # Open image for OCR
    with open(local_image_path, "rb") as image_stream:
        read_response = vision_client.read_in_stream(
            image_stream,
            raw=True
        )

    # Get operation ID
    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # -----------------------------
    # Wait for OCR result
    # -----------------------------
    while True:
        result = vision_client.get_read_result(operation_id)
        if result.status not in ["notStarted", "running"]:
            break
        time.sleep(1)

    # -----------------------------
    # Extract text
    # -----------------------------
    extracted_text = ""

    if result.status == "succeeded":
        for page in result.analyze_result.read_results:
            for line in page.lines:
                extracted_text += line.text + "\n"

    print("Extracted Text:")
    print(extracted_text)

    # OPTIONAL:
    # Store extracted_text in Azure SQL / Cosmos DB
