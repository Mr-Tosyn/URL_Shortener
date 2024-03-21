import io
import qrcode
import os
import urllib.parse
import requests
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates
import urllib.parse
import secrets
import string
from pydantic import ValidationError
from fastapi import APIRouter, HTTPException
from url_shortener.models import CreateUrlShortener, CreateUrlShortenerResponse
from url_shortener.database import MockDBOperations
from starlette.responses import RedirectResponse
     
# Create the router
url_shortener = APIRouter()


templates = Jinja2Templates(directory="templates")
#general_pages_router = APIRouter()

# Create the database
mock_db_operations = MockDBOperations()


# This function is used to generate the short url
# Frist it validates the URL
# returns the CreatedUrlShortenerResponse

# Ensure 'static' directory exists
if not os.path.exists('static'):
    os.makedirs('static')

# Configure the 'static' directory to serve static files
url_shortener.mount("/static", StaticFiles(directory="static"), name="static")

@url_shortener.post("/create", response_model=CreateUrlShortenerResponse)
async def Enter_URL(shortner: CreateUrlShortener):
    #Validate URL
    async def validate_url(url: str):
        parsed_url = urllib.parse.urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise HTTPException(status_code=400, detail="Invalid URL")
        return url
    try:
        validated_url = await validate_url(shortner.url)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    #Shorten URL
    short_url = ""
    if validated_url:
        short_url_length = 7
        res = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                      for i in range(short_url_length))
        short_url = str(res)

        status = await mock_db_operations.add_data_to_db(url=validated_url, short_url=short_url)
        if not status:
            short_url = ""

    return CreateUrlShortenerResponse(short_url=short_url, url=validated_url)


# Get All urls from the database
@url_shortener.get("/list", response_model=list[CreateUrlShortenerResponse])
async def Fetch_History():
    # Get the data from the database
    data = await mock_db_operations.fetch_all_data() 
    # Create a list of CreateUrlShortenerResponse
    arr = []
    # Loop through the data
    for key, value in data.items():
        # Add the data to the list
        arr.append(CreateUrlShortenerResponse(short_url=key, url=value))
    # Return the list
    return arr

#Generate and download QRcode
@url_shortener.get("/generate_qr_code")
def generate_qr_code(url:str):
    qr = qrcode.QRCode(version=1, box_size=5, border=5)
    qr.add_data(url)
    qr.make()
    img = qr.make_image(fill_color='black', back_color='white')
    
    # Specify the path relative to the directory of 'main.py'
    img_path = os.path.join('static', 'shortener_qr.png')
    img.save(img_path)
    # return {"image_url": f"/{img_path}"}

    # Return the QR code file as a response to download
    return FileResponse(img_path, filename='shortener_qr.png')


# Delete the url from the database
@url_shortener.delete("/delete/{short_url}")
async def delete_short_url(short_url : str):
    # Delete the url from the database
    status = await mock_db_operations.delete_data_from_db(short_url = short_url)
    # If the url is deleted from the database, return the status
    if status:
        return {"message": "Successfully deleted"}
    else:
        # If the url is not deleted from the database, return the error message
        return {"message": "Failed to delete"}

# Redirect the user to the original url
@url_shortener.get("/test/{short_url}")
async def test(short_url : str):
    # Get the url from the database
    data = await mock_db_operations.fetch_all_data() 
    # Check if the url exists in the database
    if short_url in data:
        # redirect to this url
        url = data[short_url]
        # return the redirect response
        response = RedirectResponse(url=url)
        return response
    else:
        # return the error message
        return {"message": "Failed to fetch"}

    