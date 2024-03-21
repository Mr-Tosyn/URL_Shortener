from pydantic import BaseModel

# Define the model for the URL
class CreateUrlShortener(BaseModel):
    url: str
    # Config for pydantic to validate the data in the request body
    class Config:
        orm_mode = True

#  Define the model for the URL Response
class CreateUrlShortenerResponse(BaseModel):
    # short_url is the short url generated by the server
    short_url: str
    url: str

    # Config for pydantic to validate the data in the request body
    class Config:
        orm_mode = True
