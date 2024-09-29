from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Query
import pandas as pd
import logging
import requests

logger_file = "app.log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(logger_file)
logger.addHandler(handler)

logger.info("Starting the application")
app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def is_image(url):
    try:
        # Send a HEAD request to check only the headers, saving bandwidth
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get('Content-Type')
        
        # Check if content type starts with 'image/'
        if content_type and content_type.startswith('image/'):
            return True
        return False
    except requests.RequestException as e:
        print(f"Error checking {url}: {e}")
        return False
    
# Load the CSV file into a pandas DataFrame
df = pd.read_csv('products.csv')

# Product schema for returning data
class Product(BaseModel):
    name: str
    main_category: str
    sub_category: str
    image: str
    link: str
    ratings: float
    no_of_ratings: str
    discount_price: str
    actual_price: str

# Route to get main categories with an image
@app.get("/categories")
def get_main_categories():
    categories = df.groupby('main_category').first().reset_index()[['main_category', 'image']]

    # Filter rows where 'image' is a valid image URL
    categories = categories[categories['image'].apply(is_image)]
    
    return categories.to_dict(orient='records')

# Route to get subcategories with an image based on the main category
@app.get("/subcategories/{main_category}")
def get_subcategories(main_category: str):
    subcategories = df[df['main_category'] == main_category].groupby('sub_category').first().reset_index()[['sub_category', 'image']]
    
    # Filter rows where 'image' is a valid image URL
    subcategories = subcategories[subcategories['image'].apply(is_image)]
    
    return subcategories.to_dict(orient='records')



# Route to get products based on a subcategory
@app.get("/products/{subcategory}", response_model=list[Product])
def get_products_by_subcategory(subcategory: str, page: int = Query(1, ge=1), page_size: int = Query(48, ge=1)):
    filtered_df = df[df['sub_category'] == subcategory]
    start = (page - 1) * page_size
    end = start + page_size
    paginated_products = filtered_df.iloc[start:end].to_dict(orient='records')
    return paginated_products

# Route to get paginated products
@app.get("/products", response_model=list[Product])
def get_products(page: int = Query(1, ge=1), page_size: int = Query(48, ge=1)):
    start = (page - 1) * page_size
    end = start + page_size
    logger.info(f"Fetching products from index {start} to {end}")
    print(f"Fetching products from index {start} to {end}")
    logger.info(f"Fetching products from index {start} to {end}")
    # Ensure slicing happens correctly
    paginated_products = df.iloc[start:end].to_dict(orient='records')
    logger.info(f"Products fetched successfully")
    logger.info(f"{paginated_products}")
    # Handle case when no products are left to paginate
    if not paginated_products:
        return {"message": "No more products"}
    
    return paginated_products
